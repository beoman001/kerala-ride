from flask import Blueprint, render_template, request, flash, redirect, url_for
from kerala_ride.models import PromoOffer
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
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # In a real app we'd save this or send email
        flash('Thank you for contacting KeralaRide Connect! We will get back to you shortly.', 'success')
        return redirect(url_for('main.contact'))
        
    return render_template('contact.html')

@main_bp.route('/offers')
def offers():
    offers = PromoOffer.query.filter(PromoOffer.expiry_date > datetime.utcnow()).all()
    return render_template('offers.html', offers=offers)
