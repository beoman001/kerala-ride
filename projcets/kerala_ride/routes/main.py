from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user  # 🛡️ Track if user is logged in
from kerala_ride import db
from kerala_ride.models import PromoOffer, SupportTicket  # ✉️ Import SupportTicket model
from datetime import datetime, timezone

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Fetch active promo offers to show on landing page (Updated to timezone-aware UTC)
    offers = PromoOffer.query.filter(PromoOffer.expiry_date > datetime.now(timezone.utc)).limit(3).all()
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
    offers = PromoOffer.query.filter(PromoOffer.expiry_date > datetime.now(timezone.utc)).all()
    return render_template('offers.html', offers=offers)


# ==========================================================================
# 🔌 SOCKET.IO BACKEND ROUTER HOOKS (For reference inside your socket handler)
# ==========================================================================
"""
Add these handler structures where your Flask-SocketIO engine is initialized 
(typically in your __init__.py or a dedicated sockets.py file):

from flask_socketio import emit
from kerala_ride import socketio

@socketio.on('trigger_sos')
def handle_sos_alert(payload):
    user_identity = current_user.name if current_user.is_authenticated else "Anonymous User"
    print(f"🚨 CRITICAL SOS ALERT RECEIVED From: {user_identity}")
    print(f"📍 Coordinates mapped: Lat {payload.get('lat')}, Lng {payload.get('lng')}")
    
    # Broadcast out instantly to all connected admin operations consoles
    emit('admin_receive_sos', {
        'user': user_identity,
        'lat': payload.get('lat'),
        'lng': payload.get('lng'),
        'time': payload.get('timestamp')
    }, broadcast=True)

@socketio.on('send_message')
def handle_incoming_chat(payload):
    print(f"💬 Live chat sync payload routing: {payload.get('text')}")
    
    # Broadcast to the paired recipient path channel
    emit('receive_message', {
        'text': payload.get('text'),
        'timestamp': payload.get('timestamp')
    }, broadcast=True, include_self=False)
"""
