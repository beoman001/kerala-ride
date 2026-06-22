from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from kerala_ride.models import db, User, Driver, Vehicle, Booking, PromoOffer, AuditLog, SOSAlert, FareConfig, SupportTicket, now_utc
from datetime import timedelta
import csv
import io

admin_bp = Blueprint('admin', __name__)


def check_admin():
    """🛡️ Case-Insensitive Permission Guard Engine Verification Block"""
    if not current_user.is_authenticated or current_user.role.lower() != 'admin':
        flash('Access denied. Administrator privileges required.', 'danger')
        return False
    return True


def log_action(action, details):
    """Create an audit log entry for admin actions."""
    log = AuditLog(user_id=current_user.id, action=action, details=details)
    db.session.add(log)


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_admin():
        return redirect(url_for('main.index'))

    total_customers = User.query.filter_by(role='customer').count()
    total_drivers = User.query.filter_by(role='driver').count()
    approved_drivers = Driver.query.filter_by(verification_status='Approved').count()
    pending_approvals = Driver.query.filter_by(verification_status='Pending').count()
    total_bookings = Booking.query.count()
    total_tickets = SupportTicket.query.count()

    # ⚡ SAFE FIX: Fallback arithmetic casting logic handles NULL fields cleanly
    completed_bookings = Booking.query.filter_by(status='Completed').all()
    total_revenue = sum((float(b.final_fare or b.estimated_fare or 0.0)) for b in completed_bookings)

    active_sos = SOSAlert.query.filter_by(status='Active').order_by(SOSAlert.triggered_at.desc()).all()
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()

    # ⚡ SAFE FIX: Hardened district lookup prevents dictionary unpack execution faults
    district_counts = {}
    for d in Driver.query.all():
        if d.district and d.district.strip():
            district_name = d.district.strip()
            district_counts[district_name] = district_counts.get(district_name, 0) + 1
        else:
            district_counts['Unassigned'] = district_counts.get('Unassigned', 0) + 1

    return render_template(
        'admin/dashboard.html',
        total_customers=total_customers,
        total_drivers=total_drivers,
        approved_drivers=approved_drivers,
        pending_approvals=pending_approvals,
        total_bookings=total_bookings,
        total_tickets=total_tickets,
        total_revenue=round(total_revenue, 2),
        active_sos=active_sos,
        recent_logs=recent_logs,
        district_counts=district_counts
    )


@admin_bp.route('/verification')
@login_required
def verification():
    if not check_admin():
        return redirect(url_for('main.index'))
    pending_drivers = Driver.query.filter_by(verification_status='Pending').all()
    return render_template('admin/verification.html', pending_drivers=pending_drivers)


@admin_bp.route('/verify/<int:driver_id>', methods=['POST'])
@login_required
def verify_driver(driver_id):
    if not check_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    driver = db.session.get(Driver, driver_id)
    if not driver:
        return jsonify({'error': 'Driver not found'}), 404
    action = request.form.get('action')
    reason = request.form.get('reason', '').strip()

    if action == 'approve':
        driver.verification_status = 'Approved'
        for vehicle in driver.vehicles:
            vehicle.verification_status = 'Approved'
        log_action("Approve Driver", f"Approved driver {driver.user.name} (ID: {driver.id}) and their vehicles.")
        db.session.commit()
        flash(f"Driver {driver.user.name} approved successfully.", "success")

    elif action == 'reject':
        if not reason:
            flash('A rejection reason is required.', 'danger')
            return redirect(url_for('admin.verification'))
        driver.verification_status = 'Rejected'
        driver.rejection_reason = reason
        for vehicle in driver.vehicles:
            vehicle.verification_status = 'Rejected'
        log_action("Reject Driver", f"Rejected driver {driver.user.name} (ID: {driver.id}). Reason: {reason}")
        db.session.commit()
        flash(f"Driver {driver.user.name} rejected. Reason: {reason}", "warning")

    return redirect(url_for('admin.verification'))


@admin_bp.route('/campaigns', methods=['GET', 'POST'])
@login_required
def campaigns():
    if not check_admin():
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()
        if not subject or not body:
            flash('Campaign subject and body are required.', 'danger')
            return redirect(url_for('admin.campaigns'))
        customers_count = User.query.filter_by(role='customer').count()
        log_action("Send Email Campaign", f"Dispatched campaign: '{subject}' to {customers_count} customers.")
        db.session.commit()
        flash(f"Campaign sent to {customers_count} customers! (Simulated)", "success")
        return redirect(url_for('admin.campaigns'))
    promos = PromoOffer.query.order_by(PromoOffer.created_at.desc()).all()
    customers_count = User.query.filter_by(role='customer').count()
    return render_template('admin/campaigns.html', promos=promos, customers_count=customers_count)


@admin_bp.route('/add-promo', methods=['POST'])
@login_required
def add_promo():
    if not check_admin():
        return redirect(url_for('main.index'))
    code = request.form.get('code', '').strip().upper()
    desc = request.form.get('description', '').strip()
    discount = request.form.get('discount_percentage', type=float)
    days = request.form.get('valid_days', type=int, default=7)
    if not code or not desc or discount is None:
        flash('Invalid promo details.', 'danger')
        return redirect(url_for('admin.campaigns'))
    if PromoOffer.query.filter_by(code=code).first():
        flash(f'Promo code {code} already exists.', 'warning')
        return redirect(url_for('admin.campaigns'))
    promo = PromoOffer(code=code, description=desc, discount_percentage=discount,
                       expiry_date=now_utc() + timedelta(days=days))
    db.session.add(promo)
    log_action("Create Promo", f"Created promo code {code} ({discount}% off, valid {days} days).")
    db.session.commit()
    flash(f"Promo code {code} created!", "success")
    return redirect(url_for('admin.campaigns'))


@admin_bp.route('/delete-promo/<int:promo_id>', methods=['POST'])
@login_required
def delete_promo(promo_id):
    if not check_admin():
        return redirect(url_for('main.index'))
    promo = db.session.get(PromoOffer, promo_id)
    if not promo:
        flash('Promo not found.', 'danger')
        return redirect(url_for('admin.campaigns'))
    code = promo.code
    db.session.delete(promo)
    log_action("Delete Promo", f"Deleted promo code {code}.")
    db.session.commit()
    flash(f"Promo code {code} deleted.", "success")
    return redirect(url_for('admin.campaigns'))


@admin_bp.route('/export-emails')
@login_required
def export_emails():
    if not check_admin():
        return redirect(url_for('main.index'))
    customers = User.query.filter_by(role='customer').all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Email', 'Phone', 'Joined Date'])
    for c in customers:
        writer.writerow([c.name, c.email, c.phone, c.created_at.strftime('%Y-%m-%d')])
    log_action("Export Customer Emails", "Exported customer mailing list to CSV.")
    db.session.commit()
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=customer_emails.csv"
    return response


@admin_bp.route('/resolve-sos/<int:alert_id>', methods=['POST'])
@login_required
def resolve_sos(alert_id):
    if not check_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    alert = db.session.get(SOSAlert, alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    alert.status = 'Resolved'
    log_action("Resolve SOS", f"Marked SOS Alert (ID: {alert.id}, Booking: {alert.booking_id}) as Resolved.")
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'SOS alert resolved.'})


@admin_bp.route('/fares', methods=['GET', 'POST'])
@login_required
def manage_fares():
    if not check_admin():
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        if not category:
            flash('Please select a vehicle category.', 'danger')
            return redirect(url_for('admin.manage_fares'))
        config = FareConfig.query.filter_by(vehicle_category=category).first()
        if not config:
            config = FareConfig(vehicle_category=category)
            db.session.add(config)
        config.base_fare = request.form.get('base_fare', type=float)
        config.base_distance_km = request.form.get('base_distance_km', type=float)
        config.rate_per_km = request.form.get('rate_per_km', type=float)
        log_action("Update Fares", f"Updated fares for {category}: Base ₹{config.base_fare} / {config.base_distance_km}km, then ₹{config.rate_per_km}/km.")
        db.session.commit()
        flash(f"Fare configuration for {category} updated!", "success")
        return redirect(url_for('admin.manage_fares'))
    configs = FareConfig.query.all()
    return render_template('admin/fares.html', configs=configs)


@admin_bp.route('/tickets')
@login_required
def view_tickets():
    """Secure dashboard module to read all user incoming support portal inquiries."""
    if not check_admin():
        return redirect(url_for('main.index'))
    
    tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
    return render_template('admin/tickets.html', tickets=tickets)


@admin_bp.route('/export-spatial-gaps')
@login_required
def export_spatial_gaps():
    """
    Exports booking geometric coordinates to an analytics-grade CSV dataset.
    Directly compatible with QGIS and NetworkX path tracking architectures.
    """
    if not check_admin():
        return redirect(url_for('main.index'))
        
    bookings = Booking.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Booking_ID', 'Customer_ID', 'Vehicle_Category', 
        'Pickup_Location', 'Destination_Location', 
        'Estimated_Fare', 'Status', 'Timestamp'
    ])
    
    for b in bookings:
        writer.writerow([
            b.id, b.customer_id, b.vehicle_category,
            b.pickup_location, b.destination_location,
            b.estimated_fare, b.status, b.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
        
    log_action("Export Spatial Gaps", "Exported spatial logistics network layout for QGIS graph mapping.")
    db.session.commit()
    
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=keralaride_spatial_gaps.csv"
    return response
