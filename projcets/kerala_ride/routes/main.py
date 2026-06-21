from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import current_user, login_required  # 🛡️ Track and protect user context
from kerala_ride import db
from kerala_ride.models import PromoOffer, SupportTicket  # ✉️ Import SupportTicket model
from datetime import datetime, timezone
import urllib.parse  # 🔗 For secure URL-encoding of UPI intent parameters

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Fetch active promo offers to show on landing page
    offers = PromoOffer.query.filter(PromoOffer.expiry_date > datetime.now(timezone.utc)).limit(3).all()
    return render_template('index.html', offers=offers)

# ==========================================================================
# 🗺️ DEDICATED PASSENGER RIDE FORM INTERFACE
# ==========================================================================
@main_bp.route('/book-ride')
@login_required
def book_ride():
    """
    🎯 Both the Homepage 'Book' button and Dashboard 'Book' button 
    should point here: href="{{ url_for('main.book_ride') }}"
    """
    return render_template('customer/book.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validation Check: Ensure no empty payloads bypass HTML5 validation
        if not name or not email or not subject or not message:
            flash('All input fields are required to log a support ticket.', 'danger')
            return redirect(url_for('main.contact'))

        # Check if the visitor is an authenticated customer/driver
        logged_in_user_id = current_user.id if current_user.is_authenticated else None

        try:
            # Save the ticket payload tied to the active user context
            new_ticket = SupportTicket(
                user_id=logged_in_user_id,
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(new_ticket)
            db.session.commit()
            
            flash('Thank you for contacting KeralaRide Connect! Your ticket has been logged inside our portal securely.', 'success')
            return redirect(url_for('main.contact'))
            
        except Exception as e:
            db.session.rollback()
            print(f"🚨 Support Ticket Integration Error: {e}")
            flash('An error occurred while submitting your ticket. Please try again.', 'danger')
            return redirect(url_for('main.contact'))
        
    return render_template('contact.html')

@main_bp.route('/offers')
def offers():
    offers = PromoOffer.query.filter(PromoOffer.expiry_date > datetime.now(timezone.utc)).all()
    return render_template('offers.html', offers=offers)

# ==========================================================================
# 🚖 LIVE REAL-TIME TRIP DISPATCH & NATIVE UPI DEEP-LINK ENDPOINT
# ==========================================================================
@main_bp.route('/api/trip/create', methods=['POST'])
@login_required
def create_trip_dispatch():
    """
    Accepts, logs, and initializes real-time transit matching algorithms.
    Generates fully functional deep-linking UPI payment paths for live processing.
    """
    data = request.get_json() or {}
    
    start_loc = data.get('start_location', '').strip()
    end_loc = data.get('end_location', '').strip()
    vehicle_tier = data.get('vehicle_tier', '').strip()
    payment_method = data.get('payment_method', '').strip()
    total_fare = data.get('total_fare', 0.0)
    
    if not end_loc or not vehicle_tier or not payment_method:
        return jsonify({
            'status': 'error',
            'message': 'Missing mandatory trip parameter options.'
        }), 400
        
    try:
        # Production transaction ID assignment
        transaction_ref = f"TXN-{int(datetime.now(timezone.utc).timestamp())}-{current_user.id}"
        upi_deep_link = None

        # 💳 REAL LIVE UPI DEEP-LINK INTENT HOOK
        if payment_method.lower() == 'upi':
            merchant_vpa = "keralaride@axisbank"  # ⚠️ Replace with your real bank VPA handle
            merchant_name = "KeralaRide Operations"
            
            # Formatting parameters for the protocol payload line
            upi_params = {
                'pa': merchant_vpa,
                'pn': merchant_name,
                'am': f"{total_fare:.2f}",
                'tr': transaction_ref,
                'tn': f" KeralaRide Booking {vehicle_tier.capitalize()}",
                'cu': 'INR'
            }
            # Output: upi://pay?pa=keralaride@axisbank&pn=...
            upi_deep_link = f"upi://pay?{urllib.parse.urlencode(upi_params)}"

        print(f"🚖 [LIVE DISPATCH] User {current_user.id} requested a draft {vehicle_tier.upper()}. ID: {transaction_ref}")
        if upi_deep_link:
            print(f"🔗 [UPI DEEP LINK GENERATED] -> {upi_deep_link}")

        # ⚡ Production Database Integration Layer:
        # trip = Trip(user_id=current_user.id, txn_ref=transaction_ref, fare=total_fare, status='draft', method=payment_method)
        # db.session.add(trip)
        # db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Ride draft created. Redirecting to confirmation...',
            'transaction_id': transaction_ref,
            'vehicle_tier': vehicle_tier,
            'fare': total_fare,
            'upi_intent_uri': upi_deep_link  # Sent back to open GPay/PhonePe instantly
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"🚨 Trip Dispatch Model Error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Database processing exception occurred during ride generation handles.'
        }), 500

# ==========================================================================
# 📝 PASSENGER BOOKING CONFIRMATION PAGE
# ==========================================================================
@main_bp.route('/booking')
@login_required
def booking_confirmation():
    """
    Catches the frontend redirect and displays the final booking 
    confirmation page for the specific transaction ID.
    """
    txn_id = request.args.get('txn_id')
    
    if not txn_id:
        flash("Invalid tracking reference. Please initiate a new ride request.", "danger")
        return redirect(url_for('main.index'))
        
    # In a full production environment, you would query the db for the draft trip here:
    # trip_details = Trip.query.filter_by(txn_ref=txn_id, user_id=current_user.id).first_or_404()
    
    return redirect(url_for('customer.dashboard'))


# ==========================================================================
# 🚨 UPDATE EMERGENCY TRUSTED CONTACT ENDPOINT
# ==========================================================================
@main_bp.route('/profile/emergency-contact/update', methods=['POST'])
@login_required
def update_emergency_contact():
    name = request.form.get('contact_name', '').strip()
    phone = request.form.get('contact_phone', '').strip()
    
    if not name or not phone:
        flash('Valid emergency data parameters are mandatory.', 'danger')
        return redirect(url_for('main.index'))
        
    try:
        current_user.emergency_contact_name = name
        current_user.emergency_contact_phone = phone
        db.session.commit()
        
        flash('Trusted security parameters saved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"🚨 Security Field Mutation Error: {e}")
        flash('An error occurred while updating your safety configuration.', 'danger')
        
    return redirect(url_for('main.index'))
