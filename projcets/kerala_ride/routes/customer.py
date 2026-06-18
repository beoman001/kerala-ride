import os
import math
import requests
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from twilio.rest import Client

# IMPORT CORE SYSTEM CONTEXT HOOKS
from kerala_ride import db, socketio, celery_app
from kerala_ride.models import Booking, SavedLocation, FareConfig, PromoOffer, EmergencyContact, Driver, User

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

def now_utc():
    """Helper method to return timezone-aware UTC datetime safely."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_straight_line_distance(lat1, lon1, lat2, lon2):
    """
    🎯 HA VERSINE MATHEMATICAL FALLBACK ENGINE:
    Calculates geographic straight-line distance over the Earth's radius in kilometers.
    Guarantees that route calculation can never crash your booking funnel.
    """
    R = 6371.0  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return round(R * c, 1)


def send_sms_alert(to_phone, message_body):
    """
    📱 Twilio SMS Gateway Dispatcher:
    Sends an instant text notification securely utilizing system environment configuration keys.
    """
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not account_sid or not auth_token or not twilio_number:
        print("⚠️ SMS Warning: Twilio environment keys are missing. Skipping dispatch.")
        return False

    try:
        client = Client(account_sid, auth_token)
        # Standardize number formatting to follow E.164 requirements for India (+91)
        formatted_phone = to_phone if to_phone.startswith('+') else f"+91{to_phone}"
        
        client.messages.create(
            body=message_body,
            from_=twilio_number,
            to=formatted_phone
        )
        print(f"📡 SMS Dispatch Success: Alert shot to {formatted_phone}")
        return True
    except Exception as sms_err:
        print(f"❌ Twilio API Dispatch Error: {sms_err}")
        return False


# ==========================================
# 🚀 ENTERPRISE UPGRADE: ATOMIC ROW-LOCKED BACKGROUND WORKER
# ==========================================
@celery_app.task
def processed_delayed_sms_broadcast(booking_id, district, vehicle_cat):
    """
    🎯 Celery Task Engine:
    Executes in isolation on your backend background worker container.
    Utilizes database row-locking rules to check booking statuses safely.
    """
    try:
        # 🛡️ PESSIMISTIC ROW LOCK: select ... for update locks this row until the transaction finishes
        check_booking = db.session.query(Booking).filter_by(id=booking_id).with_for_update().first()
        
        # 💰 WALLET SAVER CHECK: If a driver claimed the job over WebSockets, drop execution instantly
        if not check_booking or check_booking.status != "Pending":
            print(f"💰 Celery Savings Rule: Booking ID {booking_id} has already been claimed. Aborting SMS.")
            db.session.commit()
            return

        print(f"📡 30s Grace Timeout. Firing geo-targeted fallback SMS loop for Booking ID {booking_id}...")

        if district:
            available_drivers = Driver.query.filter(
                Driver.verification_status == 'Approved',
                Driver.is_online == True,
                Driver.district.ilike(f"%{district}%")
            ).all()
        else:
            available_drivers = Driver.query.filter(
                Driver.verification_status == 'Approved',
                Driver.is_online == True
            ).limit(5).all()

        sms_message = (
            f"KeralaRide Alert! High Priority {check_booking.type.upper()} job available.\n"
            f"Fare: ₹{check_booking.estimated_fare}\n"
            f"Vehicle: {check_booking.vehicle_category}\n"
            f"Open your dashboard now to claim this ride!"
        )

        for driver in available_drivers:
            has_matching_vehicle = any(v.category == vehicle_cat for v in driver.vehicles)
            if has_matching_vehicle and driver.user and driver.user.phone:
                send_sms_alert(driver.user.phone, sms_message)
                
        # Commit row lock parameters cleanly
        db.session.commit()

    except Exception as queue_err:
        db.session.rollback()
        print(f"❌ Celery Background Worker Failure: {queue_err}")


# ==========================================
# 1. CUSTOMER BOOKING PAGE ROUTE (CELERY ENABLED)
# ==========================================
@customer_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        booking_type = request.form.get('booking_type', 'passenger')
        pickup = request.form.get('pickup', '').strip()
        destination = request.form.get('destination', '').strip()
        vehicle_category = request.form.get('vehicle_category')
        payment_method = request.form.get('payment_method', 'Cash')
        promo_code = request.form.get('promo_code', '').strip().upper()
        estimated_fare = request.form.get('estimated_fare', 0.0)
        
        # Target specific district context sent from the front-end layout map picker
        pickup_district = request.form.get('pickup_district', '').strip()

        # Goods cargo details
        material_description = request.form.get('material_description', '').strip()
        weight = request.form.get('weight')

        if not pickup or not destination or not vehicle_category:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('customer.book'))

        try:
            # Map parameters perfectly to your database model columns
            new_booking = Booking(
                customer_id=current_user.id,
                type=booking_type,
                pickup_location=pickup,
                destination_location=destination,
                vehicle_category=vehicle_category,
                payment_method=payment_method,
                estimated_fare=float(estimated_fare),
                material_description=material_description if booking_type == 'goods' else None,
                weight=float(weight) if (booking_type == 'goods' and weight) else None,
                status="Pending"
            )

            db.session.add(new_booking)
            db.session.commit()

            # --- ⚡ STEP 1: FREE INSTANT WEBSOCKET PING TO ALL ONLINE DRIVERS ⚡ ---
            socketio.emit('new_ride_request', {
                'trip_id': new_booking.id,
                'type': new_booking.type,
                'pickup': new_booking.pickup_location,
                'dropoff': new_booking.destination_location,
                'fare': new_booking.estimated_fare,
                'cargo_desc': new_booking.material_description,
                'weight': new_booking.weight
            })

            # --- 📲 STEP 2: OFF-LOAD 30-SECOND TIMER TO CELERY CLOUD TASK QUEUE 📲 ---
            processed_delayed_sms_broadcast.apply_async(
                args=[new_booking.id, pickup_district, new_booking.vehicle_category],
                countdown=30  # Forces Celery to wait exactly 30 seconds before worker execution
            )

            flash("Your ride request is live! Local drivers are checking their dashboards.", "success")
            return redirect(url_for('customer.dashboard'))

        except Exception as e:
            db.session.rollback()
            print(f"Database Insertion Error: {e}")
            flash("An error occurred while creating your booking. Please try again.", "danger")
            return redirect(url_for('customer.book'))

    locations = []
    try:
        locations = SavedLocation.query.filter_by(user_id=current_user.id).all()
    except Exception as e:
        print(f"Error loading saved locations: {e}")

    return render_template('customer/book.html', locations=locations)


# ==========================================
# 2. DYNAMIC FARE ESTIMATOR (WITH MATH FALLB ACK PROVISIONS)
# ==========================================
@customer_bp.route('/estimate-fare', methods=['POST'])
@login_required
def estimate_fare():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Invalid payload configuration."}), 400

    pickup = data.get('pickup', '').strip()
    destination = data.get('destination', '').strip()
    category = data.get('category')
    promo_code = data.get('promo_code', '').strip().upper()

    if not pickup or not destination or not category:
        return jsonify({"success": False, "error": "Missing pickup, dropoff, or vehicle parameters."}), 400

    pickup_parts = pickup.split(',')
    dest_parts = destination.split(',')
    
    if len(pickup_parts) != 2 or len(dest_parts) != 2:
        return jsonify({"success": False, "error": "Please choose precise locations from the interactive map canvas."}), 400

    try:
        # Convert map coordinates safely to structured floats for OSRM / Haversine processing
        p_lat, p_lng = float(pickup_parts[0].strip()), float(pickup_parts[1].strip())
        d_lat, d_lng = float(dest_parts[0].strip()), float(dest_parts[1].strip())
    except ValueError:
         return jsonify({"success": False, "error": "Coordinates must match structured numeric values."}), 400

    route_geometry = None
    distance_km = 0.0

    try:
        pickup_lng_lat = f"{p_lng},{p_lat}"
        dest_lng_lat = f"{d_lng},{d_lat}"

        url = f"http://router.project-osrm.org/route/v1/driving/{pickup_lng_lat};{dest_lng_lat}"
        response = requests.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=4)
        res_data = response.json()

        if response.status_code == 200 and res_data.get('code') == 'Ok':
            distance_meters = res_data['routes'][0]['distance']
            distance_km = round(distance_meters / 1000.0, 1)
            route_geometry = res_data['routes'][0]['geometry']
        else:
            raise Exception("OSRM API returned non-optimal track code sequence.")

    except Exception as e:
        print(f"⚠️ OSRM Engine Unavailable ({str(e)}). Engaging straight-line Haversine mathematical fallback.")
        # Calculate mathematical as-the-crow-flies distance to bypass cloud routing downtimes
        distance_km = calculate_straight_line_distance(p_lat, p_lng, d_lat, d_lng)
        
        # Draw a fallback vector line directly connecting the pin inputs on Leaflet
        route_geometry = {
            "type": "LineString",
            "coordinates": [[p_lng, p_lat], [d_lng, d_lat]]
        }

    # Default fallback rulesets if admin hasn't set custom database entries yet
    admin_base_fare = 60.0
    admin_minimum_km = 3.0
    admin_rate_per_km = 15.0

    try:
        # Pull the live parameters set by the admin for this specific vehicle category
        fare_config = FareConfig.query.filter_by(vehicle_category=category).first()
        if fare_config:
            admin_base_fare = float(fare_config.base_fare)
            admin_minimum_km = float(fare_config.base_distance_km)
            admin_rate_per_km = float(fare_config.rate_per_km)
    except Exception as db_err:
        print(f"Database check exception, relying on presets: {db_err}")

    print(f"\n--- DEBUG: ADMIN-DRIVEN FARE CALCULATOR ---")
    print(f"Vehicle Category: {category} | Distance Matrix: {distance_km} km")
    print(f"Admin Configs -> Flat Base Charge: ₹{admin_base_fare} | Below Minimum Limit: {admin_minimum_km} km")

    forward_fare = 0.0
    return_charge = 0.0
    is_outstation = False

    if distance_km <= admin_minimum_km:
        print(f"RESULT: Distance is below minimum limit. Locking forward fare to base: ₹{admin_base_fare}")
        forward_fare = admin_base_fare
        return_charge = 0.0
    else:
        print(f"RESULT: Distance exceeds minimum limit. Appending extra mileage meters.")
        billable_extra_km = distance_km - admin_minimum_km
        forward_fare = admin_base_fare + (billable_extra_km * admin_rate_per_km)
        
        if distance_km > 500.0:
            is_outstation = True
            return_charge = distance_km * admin_rate_per_km
        else:
            return_charge = forward_fare

    final_fare = forward_fare + return_charge

    discount = 0.0
    if promo_code:
        try:
            promo = PromoOffer.query.filter_by(code=promo_code).first()
            if promo and not promo.is_expired:
                discount = round(final_fare * (promo.discount_percentage / 100.0), 2)
                final_fare -= discount
        except Exception as promo_err:
            print(f"Promo extraction check failure: {promo_err}")

    final_fare = max(0.0, round(final_fare, 2))

    print(f"Forward Step: ₹{forward_fare} | Return Step: ₹{return_charge} | Final Payable: ₹{final_fare}")
    print(f"-----------------------------------------\n")

    return jsonify({
        "success": True,
        "distance_km": distance_km,
        "base_fare": admin_base_fare,
        "base_distance": admin_minimum_km,
        "rate_per_km": admin_rate_per_km,
        "return_charge": return_charge,
        "discount": discount,
        "final_fare": final_fare,
        "promo_applied": True if discount > 0 else False,
        "is_outstation": is_outstation,
        "route_geometry": route_geometry
    })


# ==========================================
# 3. CUSTOMER DASHBOARD & CANCELLATION ENGINE
# ==========================================
@customer_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        user_bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(Booking.id.desc()).all()
    except Exception as e:
        print(f"Error loading dashboard bookings: {e}")
        user_bookings = []
    return render_template('customer/dashboard.html', bookings=user_bookings)


@customer_bp.route('/cancel-ride/<int:booking_id>', methods=['POST'])
@login_required
def cancel_ride(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.customer_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('customer.dashboard'))

    if booking.status != "Pending":
        flash("You can only cancel rides that are currently Pending.", "warning")
        return redirect(url_for('customer.dashboard'))

    try:
        minutes_passed = (now_utc() - booking.created_at).total_seconds() / 60.0
    except Exception:
        minutes_passed = 0

    if minutes_passed > 15.0:
        penalty = round(float(booking.estimated_fare) * 0.25, 2)
        booking.status = "Cancelled"
        booking.final_fare = penalty
        flash(f"Ride cancelled. A 1/4 grace penalty (₹{penalty}) has been applied.", "info")
    else:
        booking.status = "Cancelled"
        booking.final_fare = 0.0
        flash("Your ride has been cancelled successfully.", "success")

    db.session.commit()
    return redirect(url_for('customer.dashboard'))


# ==========================================
# 4. SAVE NEW LOCATION ROUTE
# ==========================================
@customer_bp.route('/add-location', methods=['POST'])
@login_required
def add_location():
    label = request.form.get('label', '').strip()
    address = request.form.get('address', '').strip()

    if not label or not address:
        flash("Label and Address parameters are required.", "danger")
        return redirect(url_for('customer.book'))

    try:
        new_loc = SavedLocation(
            user_id=current_user.id,
            label=label,
            address=address
        )
        db.session.add(new_loc)
        db.session.commit()
        flash("Location saved successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error saving location parameters: {e}")
        flash("Could not save location configurations.", "danger")

    return redirect(url_for('customer.book'))


# ==========================================
# 5. ADD EMERGENCY CONTACT ROUTE
# ==========================================
@customer_bp.route('/add-contact', methods=['POST'])
@login_required
def add_contact():
    contact_name = request.form.get('contact_name', '').strip()
    contact_phone = request.form.get('contact_phone', '').strip()

    if not contact_name or not contact_phone:
        flash("Contact Name and Phone Number are required fields.", "danger")
        return redirect(url_for('customer.dashboard'))

    try:
        new_contact = EmergencyContact(
            user_id=current_user.id,
            name=contact_name,
            phone=contact_phone
        )
        db.session.add(new_contact)
        db.session.commit()
        flash("Emergency contact added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error saving emergency contact structural values: {e}")
        flash("Could not save the requested contact configuration.", "danger")

    return redirect(url_for('customer.dashboard'))
