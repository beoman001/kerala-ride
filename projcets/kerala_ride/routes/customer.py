import os
import requests
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from kerala_ride import db
from kerala_ride.models import Booking, SavedLocation, FareConfig, PromoOffer, EmergencyContact

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

def now_utc():
    """Helper method to return timezone-aware UTC datetime safely for SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ==========================================
# 1. CUSTOMER BOOKING PAGE ROUTE
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
            flash("Your ride request has been submitted successfully!", "success")
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
# 2. FREE OPENSTREETMAP FARE ESTIMATOR
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

    route_geometry = None
    try:
        pickup_parts = pickup.split(',')
        dest_parts = destination.split(',')
        
        if len(pickup_parts) != 2 or len(dest_parts) != 2:
            return jsonify({"success": False, "error": "Please choose precise locations from the interactive map canvas."}), 400

        pickup_lng_lat = f"{pickup_parts[1].strip()},{pickup_parts[0].strip()}"
        dest_lng_lat = f"{dest_parts[1].strip()},{dest_parts[0].strip()}"

        url = f"http://router.project-osrm.org/route/v1/driving/{pickup_lng_lat};{dest_lng_lat}"
        response = requests.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=5)
        res_data = response.json()

        if res_data.get('code') == 'Ok':
            distance_meters = res_data['routes'][0]['distance']
            distance_km = round(distance_meters / 1000.0, 1)
            route_geometry = res_data['routes'][0]['geometry']
        else:
            return jsonify({"success": False, "error": "Could not map a driving route layout."}), 400

    except Exception as e:
        print(f"OSRM Routing Server Failure: {e}")
        return jsonify({"success": False, "error": "Free routing engine timed out."}), 500

    # Default application presets fallback if database configs are empty
    base_fare = 60.0
    base_distance = 3.0
    rate_per_km = 15.0

    try:
        fare_config = FareConfig.query.filter_by(vehicle_category=category).first()
        if fare_config:
            base_fare = float(fare_config.base_fare)
            base_distance = float(fare_config.base_distance_km)
            rate_per_km = float(fare_config.rate_per_km)
    except Exception as db_err:
        print(f"Database check exception, relying on presets: {db_err}")

    # ==========================================
    # STEP-BY-STEP FARE COMPUTATION (GLOBAL MINIMUM KM BLOCK)
    # ==========================================
    print(f"\n--- DEBUG: UNIVERSAL FARE CALCULATION ---")
    print(f"Calculated Road Distance: {distance_km} km")
    print(f"Selected Category: {category}")
    
    forward_fare = 0.0
    return_charge = 0.0
    is_outstation = False

    # 1. SPECIAL CASE PACKAGE FOR 8-SEATER SUV (UP TO 80 KM PACKAGE)
    if category == "8-Seater SUV":
        FIXED_MAX_KM = 80.0
        FIXED_PRICE = 3500.0
        
        if distance_km <= FIXED_MAX_KM:
            forward_fare = FIXED_PRICE
        else:
            extra_km = distance_km - FIXED_MAX_KM
            forward_fare = FIXED_PRICE + (extra_km * rate_per_km)
            
    # 2. STANDARD PRICING METHOD FOR ALL OTHER VEHICLE FIELDS
    else:
        if distance_km <= base_distance:
            forward_fare = base_fare
        else:
            billable_extra_km = distance_km - base_distance
            forward_fare = base_fare + (billable_extra_km * rate_per_km)

    # 3. UNIVERSAL RETURN CHARGE SAFETY BOUNDARY FOR ALL VEHICLES
    # Return charge drops completely to zero if trip stays within this local limit
    MIN_KM_FOR_RETURN = 15.0 

    if distance_km > 500.0:
        is_outstation = True
        return_charge = distance_km * rate_per_km
    elif distance_km > MIN_KM_FOR_RETURN:
        # Long trip triggered: Return fee matches forward fare across the system
        return_charge = forward_fare
    else:
        # Short local trip under the threshold: Return charges dropped completely to zero!
        print(f"RESULT: Trip (≤ {MIN_KM_FOR_RETURN}km) is local. Zeroing return charges.")
        return_charge = 0.0

    # 4. COMBINE SUB-COMPONENTS FOR TOTAL FARE
    final_fare = forward_fare + return_charge

    # Promo Offer System Checks
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

    print(f"Forward Base: {forward_fare} | Return Loop Cost: {return_charge} | Final: {final_fare}")
    print(f"-----------------------------------\n")

    return jsonify({
        "success": True,
        "distance_km": distance_km,
        "base_fare": base_fare,
        "base_distance": base_distance,
        "rate_per_km": rate_per_km,
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
# 4. SAVE NEW LOCATION ROUTE (FIX FOR BUILDERROR)
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
# 5. ADD EMERGENCY CONTACT ROUTE (FIX FOR BUILDERROR)
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
