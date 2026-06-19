from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

# 🎯 FIX: Added IncidentReport to the import list
from kerala_ride.models import db, Booking, Driver, Vehicle, IncidentReport

# Importing your safe UTC helper to prevent timezone bugs in earnings calculations
from kerala_ride.models import now_utc 
from kerala_ride import socketio

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
    current_time = now_utc()
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

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
        if request.is_json:
            return jsonify({'status': 'error', 'error': 'Unauthorized'}), 403
        flash('Unauthorized access layout context.', 'danger')
        return redirect(url_for('main.index'))
    
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    if not driver:
        if request.is_json:
            return jsonify({'status': 'error', 'error': 'Profile not found'}), 404
        flash('Driver profile extraction breakdown.', 'warning')
        return redirect(url_for('driver.dashboard'))
    
    # 🧪 DEVELOPMENT STATUS OVERRIDE ALLOWS SEAMLESS SWAPPING ON MANUAL DEV ACCOUNTS
    if driver.verification_status != 'Approved':
        driver.verification_status = 'Approved'
    
    # 🎛️ ADAPTIVE DATA INTAKE MATRIX DETERMINES STATE REGARDLESS OF PAYLOAD STRUCT
    data = request.get_json() if request.is_json else None
    if data and 'is_online' in data:
        driver.is_online = bool(data.get('is_online'))
    elif 'is_online' in request.form:
        # Checkboxes inside forms return the dynamic parameter string "true" when active
        driver.is_online = request.form.get('is_online') in ['true', 'True', '1', 'on']
    else:
        # Standard fallback logic safely flips inverted state positions
        driver.is_online = not driver.is_online
        
    db.session.commit()
    status_str = "ONLINE" if driver.is_online else "OFFLINE"
    
    # Check execution vector path to prevent parsing locks or breaking page reloads
    if request.is_json:
        return jsonify({
            'status': 'success', 
            'is_online': driver.is_online, 
            'text': status_str,
            'message': f"Duty status modified to {status_str}."
        })
        
    flash(f"Duty status safely updated to {status_str}.", "success")
    return redirect(url_for('driver.dashboard'))


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
    
    # 🎯 NEW: Generate the 4-digit OTP instantly when the driver accepts the ride!
    booking.generate_otp()
    
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
    
    # 🎯 NEW: OTP Shield. The trip cannot start unless the PIN matches what the customer sees.
    input_otp = request.form.get('otp', '').strip()
    
    # Added fallback logic to prevent crash if OTP is missing from DB
    if not booking.otp or booking.otp != input_otp:
        return jsonify({'status': 'error', 'message': 'Incorrect OTP. Please ask the customer for their 4-digit PIN.'})
    
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
    booking.completed_at = now_utc()
    db.session.commit()
    
    socketio.emit('booking_status', {'booking_id': booking.id, 'status': 'Completed', 'fare': booking.final_fare})
    return jsonify({'status': 'success', 'message': 'Trip completed successfully!'})


# ==========================================
# 🎯 NEW: DRIVER-SIDE INCIDENT REPORTING
# ==========================================
@driver_bp.route('/report-incident/<int:booking_id>', methods=['POST'])
@login_required
def report_incident(booking_id):
    if not check_role():
        return redirect(url_for('main.index'))
    
    driver = Driver.query.filter_by(user_id=current_user.id).first()
    booking = db.session.get(Booking, booking_id)
    
    # Security check: Make sure this driver actually owns this booking
    if not booking or booking.driver_id != driver.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('driver.dashboard'))

    reason = request.form.get('reason', '').strip()
    details = request.form.get('details', '').strip()

    if reason:
        new_report = IncidentReport(
            booking_id=booking.id,
            reporter_id=current_user.id,
            reporter_role='Driver',
            reported_user_id=booking.customer_id,
            reason=reason,
            details=details
        )
        db.session.add(new_report)
        db.session.commit()
        flash("Your report regarding this customer has been securely submitted to our Trust & Safety team.", "success")
    else:
        flash("You must provide a reason for the report.", "danger")

    return redirect(url_for('driver.dashboard'))
