import os
import requests
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from kerala_ride import db
from kerala_ride.models import Booking, SavedLocation, FareConfig # Adjust models path if yours is different

# Attempt imports for optional components; fallbacks handle missing tables gracefully
try:
    from kerala_ride.models import EmergencyContact
except ImportError:
    EmergencyContact = None

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')


# ==========================================
# 1. CUSTOMER BOOKING PAGE ROUTE
# ==========================================
@customer_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        # Retrieve form parameters submitted by book.html
        booking_type = request.form.get('booking_type')
        pickup = request.form.get('pickup', '').strip()
        destination = request.form.get('destination', '').strip()
        vehicle_category = request.form.get('vehicle_category')
        payment_method = request.form.get('payment_method')
        promo_code = request.form.get('promo_code', '').strip().upper()
        
        # Capture the dynamically calculated fare from the hidden input field
        estimated_fare = request.form.get('estimated_fare', 0.0)

        # Cargo specific items
        material_description = request.form.get('material_description', '').strip()
        weight = request.form.get('weight')

        if not pickup or not destination or not vehicle_category:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('customer.book'))

        try:
            # Create a brand new Booking transaction model instance
            new_booking = Booking(
                user_id=current_user.id,
                booking_type=booking_type,
                pickup_location=pickup,
                drop_location=destination,
                vehicle_category=vehicle_category,
                payment_method=payment_method,
                promo_code=promo_code if promo_code else None,
                estimated_fare=float(estimated_fare),  # Fare is now safely saved to DB!
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
            print(f"Database Booking Insertion Error: {e}")
            flash("An error occurred while creating your booking. Please try again.", "danger")
            return redirect(url_for('customer.book'))

    # GET Request: Fetch saved locations to display as shortcut buttons
    locations = []
    try:
        locations = SavedLocation.query.filter_by(user_id=current_user.id).all()
    except Exception as e:
        print(f"Error loading saved locations: {e}")

    return render_template('customer/book.html', locations=locations)


# ==========================================
# 2. FREE OPENSTREETMAP FARE ESTIMATOR + DYNAMIC RETURN THRESHOLD
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
            return jsonify({
                "success": False,
                "error": "Please choose precise locations from the interactive map canvas or suggestion dropdown lists."
            }), 400

        pickup_lng_lat = f"{pickup_parts[1].strip()},{pickup_parts[0].strip()}"
        dest_lng_lat = f"{dest_parts[1].strip()},{dest_parts[0].strip()}"

        # Fetch route data with 'full' geometry to draw the map lines
        url = f"http://router.project-osrm.org/route/v1/driving/{pickup_lng_lat};{dest_lng_lat}"
        response = requests.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=5)
        res_data = response.json()

        if res_data.get('code') == 'Ok':
            distance_meters = res_data['routes'][0]['distance']
            distance_km = round(distance_meters / 1000.0, 1)
            route_geometry = res_data['routes'][0]['geometry']
        else:
            return jsonify({"success": False, "error": "Could not map a driving route layout between those selected points."}), 400

    except Exception as e:
        print(f"OSRM Routing Server Failure: {e}")
        return jsonify({"success": False, "error": "Free routing engine timed out. Please try again shortly."}), 500

    # QUERY RATES MATRIX FROM DATABASE OR CONFIGURE SYSTEM DEFAULT FALLBACKS
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
        print(f"Database check caught an exception, relying on application presets: {db_err}")

    # ==========================================
    # STEP-BY-STEP FARE COMPUTATION (MINIMUM KM FIX)
    # ==========================================
    print(f"\n--- DEBUG: NEW FARE CALCULATION ---")
    print(f"Calculated Road Distance: {distance_km} km")
    
    is_outstation = False
    return_charge = 0.0
    forward_fare = 0.0
    
    # 1. THE GOING CHARGE IS ALWAYS NORMAL (Base Fare + Extra KM)
    if distance_km <= base_distance:
        forward_fare = base_fare
    else:
        billable_extra_km = distance_km - base_distance
        forward_fare = base_fare + (billable_extra_km * rate_per_km)

    # 2. CALCULATE THE RETURN CHARGE WITH A MINIMUM DISTANCE THRESHOLD
    # Adjust this value to set the minimum distance required to trigger a return fee
    MIN_KM_FOR_RETURN = 15.0 

    if distance_km > 500.0:
        is_outstation = True
        print("RESULT: Outstation Rule Triggered (>500km)!")
        # Above 500km: Return case ONLY uses the flat rate per km. No base fare added.
        return_charge = distance_km * rate_per_km
    elif distance_km > MIN_KM_FOR_RETURN:
        print(f"RESULT: Return Rule Triggered (Between {MIN_KM_FOR_RETURN}km and 500km)")
        # If it's a long trip but below outstation tier, the return charge matches the going charge
        return_charge = forward_fare
    else:
        print(f"RESULT: Ultra-Short Local Trip (≤ {MIN_KM_FOR_RETURN}km). NO return charge added.")
        # Under the minimum km threshold? Return charge stays exactly 0.0!
        return_charge = 0.0

    # 3. COMBINE FOR TOTAL ESTIMATE
    final_fare = forward_fare + return_charge

    # PROMO COUPON SYSTEM REDUCTION RULES
    discount = 0.0
    if promo_code == "KERALA50":
        discount = round(final_fare * 0.50, 2)
        if discount > 100.0:
            discount = 100.0
        final_fare -= discount

    final_fare = max(0.0, round(final_fare, 2))
    
    print(f"Forward Fare: {forward_fare} | Return Charge: {return_charge} | Total Fare: {final_fare}")
    print(f"Final Fare Sent to Browser: ₹{final_fare}")
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
# 3. CUSTOMER DASHBOARD ROUTE
# ==========================================
@customer_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.id.desc()).all()
    except Exception as e:
        print(f"Error loading dashboard bookings: {e}")
        user_bookings = []

    return render_template('customer/dashboard.html', bookings=user_bookings)


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
        print(f"Error saving location target parameters: {e}")
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
    relationship = request.form.get('relationship', '').strip()

    if not contact_name or not contact_phone:
        flash("Contact Name and Phone Number are required fields.", "danger")
        return redirect(url_for('customer.dashboard'))

    if EmergencyContact is None:
        print("EmergencyContact table model does not exist or is unimported inside models runtime.")
        flash("Emergency contact database layout is unavailable right now.", "danger")
        return redirect(url_for('customer.dashboard'))

    try:
        new_contact = EmergencyContact(
            user_id=current_user.id,
            name=contact_name,
            phone=contact_phone,
            relationship=relationship if relationship else None
        )
        db.session.add(new_contact)
        db.session.commit()
        flash("Emergency contact added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error saving emergency contact structural values: {e}")
        flash("Could not save the requested contact configuration.", "danger")

    return redirect(url_for('customer.dashboard'))


# ==========================================
# 6. CANCEL RIDE & PENALTY ROUTE
# ==========================================
@customer_bp.route('/cancel-ride/<int:booking_id>', methods=['POST'])
@login_required
def cancel_ride(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Security check
    if booking.user_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('customer.dashboard'))

    if booking.status != "Pending":
        flash("You can only cancel rides that are currently Pending.", "warning")
        return redirect(url_for('customer.dashboard'))

    # Calculate time difference in minutes
    try:
        minutes_passed = (datetime.utcnow() - booking.created_at).total_seconds() / 60.0
    except Exception:
        minutes_passed = 0 # Fallback if database lacks created_at timestamp

    message = "Your ride has been cancelled successfully."
    
    # Check the 15-minute rule
    if minutes_passed > 15.0:
        # Calculate 1/4th (25%) of the total estimated fare
        penalty = round(float(booking.estimated_fare) * 0.25, 2)
        
        # Mark as cancelled with penalty string
        booking.status = f"Cancelled (Penalty: ₹{penalty})"
        message = f"Ride cancelled. Since 15 minutes passed, a 1/4 penalty charge (₹{penalty}) will be added to your account for the driver's wasted time."
    else:
        booking.status = "Cancelled"

    try:
        db.session.commit()
        flash(message, "info")
    except Exception as e:
        db.session.rollback()
        flash("Error cancelling ride.", "danger")

    return redirect(url_for('customer.dashboard'))
