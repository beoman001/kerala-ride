from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from kerala_ride.models import db, Booking, Driver, Vehicle
from kerala_ride import socketio
from datetime import datetime

driver_bp = Blueprint('driver', __name__)


def check_role():
    if current_user.role != 'driver':
        flash('Access denied. Driver account required.', 'danger')
        return False
    return True


@driver_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_role():
        return redirect(url_for('main.index'))

    driver = Driver.query.filter_by(user_id=current_user.id).first()
    if not driver:
        flash('Driver profile not found. Please register.', 'warning')
        return redirect(url_for('auth.driver_register'))

    vehicle = Vehicle.query.filter_by(driver_id=driver.id).first()

    # Earnings — use final_fare for accuracy, fall back to estimated_fare
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    today_bookings = Booking.query.filter(
        Booking.driver_id == driver.id,
        Booking.status == 'Completed',
        Booking.completed_at >= today_start
    ).all()
    today_earnings = sum((b.final_fare or b.estimated_fare) for b in today_bookings)

    month_bookings = Booking.query.filter(
        Booking.driver_id == driver.id,
        Booking.status == 'Completed',
        Booking.completed_at >= month_start
    ).all()
    month_earnings = sum((b.final_fare or b.estimated_fare) for b in month_bookings)

    completed_trips_count = Booking.query.filter(
        Booking.driver_id == driver.id,
        Booking.status == 'Completed'
    ).count()

    active_booking = Booking.query.filter(
        Booking.driver_id == driver.id,
        Booking.status.in_(['Accepted', 'Arrived', 'Active'])
    ).first()

    trip_history = Booking.query.filter(
        Booking.driver_id == driver.id,
        Booking.status.in_(['Completed', 'Cancelled'])
    ).order_by(Booking.created_at.desc()).limit(10).all()

    pending_bookings = []
    if driver.verification_status == 'Approved' and driver.is_online:
        pending_bookings = Booking.query.filter(
            Booking.status == 'Pending',
            Booking.vehicle_category == (vehicle.category if vehicle else 'Auto Rickshaw')
        ).all()

    return render_template(
        'driver/dashboard.html',
        driver=driver, vehicle=vehicle,
        today_earnings=round(today_earnings, 2),
        month_earnings=round(month_earnings, 2),
        completed_trips_count=completed_trips_count,
        active_booking=active_booking,
        trip_history=trip_history,
        pending_bookings=pending_bookings
    )


@driver_bp.route('/toggle-online', methods=['POST'])
@login_required
def toggle_online():
    if not check_role():
        return jsonify({'error': 'Unauthorized'}), 403
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    if not driver:
        return jsonify({'error': 'Profile not found'}), 404
    if driver.verification_status != 'Approved':
        return jsonify({'error': 'Driver is not approved yet.'}), 403
    driver.is_online = not driver.is_online
    db.session.commit()
    status_str = "Online" if driver.is_online else "Offline"
    return jsonify({'status': 'success', 'is_online': driver.is_online, 'message': f"You are now {status_str}."})


@driver_bp.route('/accept/<int:booking_id>', methods=['POST'])
@login_required
def accept_booking(booking_id):
    if not check_role():
        return redirect(url_for('main.index'))
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    if not driver or driver.verification_status != 'Approved':
        flash('You must be verified to accept bookings.', 'danger')
        return redirect(url_for('driver.dashboard'))
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.status != 'Pending':
        flash('This booking is no longer available.', 'warning')
        return redirect(url_for('driver.dashboard'))
    existing_active = Booking.query.filter(
        Booking.driver_id == driver.id,
        Booking.status.in_(['Accepted', 'Arrived', 'Active'])
    ).first()
    if existing_active:
        flash('You already have an active trip. Complete it first.', 'warning')
        return redirect(url_for('driver.dashboard'))
    booking.driver_id = driver.id
    booking.status = 'Accepted'
    db.session.commit()
    socketio.emit('booking_status', {
        'booking_id': booking.id,
        'status': 'Accepted',
        'driver_name': current_user.name,
        'driver_phone': current_user.phone,
        'vehicle_plate': driver.vehicles[0].plate_number if driver.vehicles else 'KL-MOCK-1234',
        'vehicle_model': f"{driver.vehicles[0].brand} {driver.vehicles[0].model}" if driver.vehicles else 'Vehicle'
    })
    flash('Booking accepted successfully!', 'success')
    return redirect(url_for('driver.dashboard'))


@driver_bp.route('/arrived/<int:booking_id>', methods=['POST'])
@login_required
def arrived(booking_id):
    if not check_role():
        return jsonify({'error': 'Unauthorized'}), 403
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.driver_id != driver.id:
        return jsonify({'error': 'Unauthorized'}), 403
    booking.status = 'Arrived'
    db.session.commit()
    socketio.emit('booking_status', {'booking_id': booking.id, 'status': 'Arrived'})
    return jsonify({'status': 'success', 'message': 'Notified customer of arrival.'})


@driver_bp.route('/start-trip/<int:booking_id>', methods=['POST'])
@login_required
def start_trip(booking_id):
    if not check_role():
        return jsonify({'error': 'Unauthorized'}), 403
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.driver_id != driver.id:
        return jsonify({'error': 'Unauthorized'}), 403
    input_otp = request.form.get('otp', '').strip()
    if booking.otp != input_otp:
        return jsonify({'status': 'error', 'message': 'Incorrect OTP. Please try again.'})
    booking.status = 'Active'
    db.session.commit()
    socketio.emit('booking_status', {'booking_id': booking.id, 'status': 'Active'})
    return jsonify({'status': 'success', 'message': 'OTP Verified! Trip started.'})


@driver_bp.route('/complete-trip/<int:booking_id>', methods=['POST'])
@login_required
def complete_trip(booking_id):
    if not check_role():
        return jsonify({'error': 'Unauthorized'}), 403
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    booking = db.session.get(Booking, booking_id)
    if not booking or booking.driver_id != driver.id:
        return jsonify({'error': 'Unauthorized'}), 403
    booking.status = 'Completed'
    booking.final_fare = booking.estimated_fare
    booking.completed_at = datetime.utcnow()
    db.session.commit()
    socketio.emit('booking_status', {'booking_id': booking.id, 'status': 'Completed', 'fare': booking.final_fare})
    return jsonify({'status': 'success', 'message': 'Trip completed successfully!'})
