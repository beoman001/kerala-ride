from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user  # 🛡️ Track if user is logged in
from kerala_ride import db
from kerala_ride.models import PromoOffer, SupportTicket  # ✉️ Import our new SupportTicket model
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Fetch active promo offers to show on landing page
    offers = PromoOffer.query.filter(PromoOffer.expiry_date > datetime.utcnow()).limit(3).all()
    return render_template('index.html', offers=offers)

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
    offers = PromoOffer.query.filter(PromoOffer.expiry_date > datetime.utcnow()).all()
    return render_template('offers.html', offers=offers)
