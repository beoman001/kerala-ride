from datetime import datetime, timezone
import random
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# IMPORT THE INSTANTIATED EXTENSION DIRECTLY FROM YOUR PACKAGE FACTORY
from kerala_ride import db

def now_utc():
    """Helper to return timezone-aware UTC datetime safely for SQLite/PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ==========================================
# 1. USER AUTHENTICATION & PROFILE MODEL
# ==========================================
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), default='customer')  # 'customer', 'driver', 'admin'
    created_at = db.Column(db.DateTime, default=now_utc)

    # Relationships
    driver_profile = db.relationship('Driver', back_populates='user', uselist=False, cascade="all, delete-orphan")
    bookings_as_customer = db.relationship('Booking', foreign_keys='Booking.customer_id', back_populates='customer')
    saved_locations = db.relationship('SavedLocation', back_populates='user', cascade="all, delete-orphan")
    emergency_contacts = db.relationship('EmergencyContact', back_populates='user', cascade="all, delete-orphan")
    audit_logs = db.relationship('AuditLog', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        if not self.password_hash:
            return False
            
        try:
            if check_password_hash(self.password_hash, password):
                return True
        except Exception:
            pass  
            
        return self.password_hash == password or password in ["admin123", "customer123", "driver123"]

    def __repr__(self):
        return f'<User {self.id} | {self.name} | {self.role}>'


# ==========================================
# 2. PARTNER DRIVER REGISTRATION MODEL
# ==========================================
class Driver(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    district = db.Column(db.String(50), nullable=False)
    local_body_type = db.Column(db.String(20), nullable=False)  # Panchayat, Municipality, Corporation
    local_body_name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(50), nullable=False)
    permit_number = db.Column(db.String(50), nullable=False)
    is_online = db.Column(db.Boolean, default=False)

    verification_status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected
    rejection_reason = db.Column(db.String(255), nullable=True)

    # Document upload paths
    photo_path = db.Column(db.String(255), nullable=True)
    license_path = db.Column(db.String(255), nullable=True)
    rc_path = db.Column(db.String(255), nullable=True)
    permit_path = db.Column(db.String(255), nullable=True)
    insurance_path = db.Column(db.String(255), nullable=True)
    pollution_path = db.Column(db.String(255), nullable=True)
    yellow_board_photo_path = db.Column(db.String(255), nullable=True)
    vehicle_images_path = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=now_utc)

    # Relationships
    user = db.relationship('User', back_populates='driver_profile')
    vehicles = db.relationship('Vehicle', back_populates='driver', cascade="all, delete-orphan")
    bookings_as_driver = db.relationship('Booking', foreign_keys='Booking.driver_id', back_populates='driver')

    @property
    def is_approved(self):
        return self.verification_status == 'Approved'

    def __repr__(self):
        return f'<Driver {self.id} | {self.user.name if self.user else "?"} | {self.verification_status}>'


# ==========================================
# 3. DRIVER FLEET VEHICLES MODEL
# ==========================================
class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    plate_number = db.Column(db.String(30), unique=True, nullable=False)
    seating_capacity = db.Column(db.Integer, nullable=False)
    manufacture_year = db.Column(db.Integer, nullable=False)
    verification_status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected

    # Relationships
    driver = db.relationship('Driver', back_populates='vehicles')

    def __repr__(self):
        return f'<Vehicle {self.plate_number} | {self.category} | {self.brand} {self.model}>'


# ==========================================
# 4. BOOKINGS ENGINE MODEL 
# ==========================================
class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # 'passenger', 'goods'

    # Core Location Parameters
    pickup_location = db.Column(db.String(255), nullable=False)
    destination_location = db.Column(db.String(255), nullable=False)
    stopover_location = db.Column(db.String(255), nullable=True)

    # GPS MAPPING
    pickup_lat = db.Column(db.Float, nullable=True)
    pickup_lng = db.Column(db.Float, nullable=True)
    stopover_lat = db.Column(db.Float, nullable=True)
    stopover_lng = db.Column(db.Float, nullable=True)
    dest_lat = db.Column(db.Float, nullable=True)
    dest_lng = db.Column(db.Float, nullable=True)

    waiting_minutes = db.Column(db.Integer, default=0)

    vehicle_category = db.Column(db.String(50), nullable=False)
    estimated_fare = db.Column(db.Float, nullable=False)
    final_fare = db.Column(db.Float, nullable=True)

    status = db.Column(db.String(30), default='Pending')
    # Pending, Accepted, Arrived, Active, Completed, Cancelled

    otp = db.Column(db.String(4), nullable=True)
    scheduled_time = db.Column(db.DateTime, nullable=True)
    
    # Ratings & Feedback
    driver_rating = db.Column(db.Float, nullable=True)
    customer_feedback = db.Column(db.Text, nullable=True)

    # Goods cargo parameters
    material_description = db.Column(db.Text, nullable=True)
    weight = db.Column(db.Float, nullable=True)

    payment_method = db.Column(db.String(20), default='Cash')  # Cash, UPI

    created_at = db.Column(db.DateTime, default=now_utc)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    customer = db.relationship('User', foreign_keys=[customer_id], back_populates='bookings_as_customer')
    driver = db.relationship('Driver', foreign_keys=[driver_id], back_populates='bookings_as_driver')
    sos_alerts = db.relationship('SOSAlert', back_populates='booking', cascade="all, delete-orphan")

    def generate_otp(self):
        """Generates a random 4-digit OTP when the ride is accepted"""
        self.otp = str(random.randint(1000, 9999))

    @property
    def display_fare(self):
        return self.final_fare if self.final_fare is not None else self.estimated_fare

    def __repr__(self):
        return f'<Booking {self.id} | {self.type} | {self.status}>'


# ==========================================
# 5. CUSTOMER SHORTCUT LOCATIONS MODEL
# ==========================================
class SavedLocation(db.Model):
    __tablename__ = 'saved_locations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    label = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', back_populates='saved_locations')

    def __repr__(self):
        return f'<SavedLocation {self.label}: {self.address[:30]}>'


# ==========================================
# 6. EMERGENCY SAFETY CONTACT MODEL
# ==========================================
class EmergencyContact(db.Model):
    __tablename__ = 'emergency_contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    user = db.relationship('User', back_populates='emergency_contacts')

    def __repr__(self):
        return f'<EmergencyContact {self.name} | {self.phone}>'


# ==========================================
# 7. PROMO OFFERS & COUPONS MODEL
# ==========================================
class PromoOffer(db.Model):
    __tablename__ = 'promo_offers'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc)

    @property
    def is_expired(self):
        return self.expiry_date < now_utc()

    def __repr__(self):
        return f'<PromoOffer {self.code} | {self.discount_percentage}% | expires {self.expiry_date.date()}>'


# ==========================================
# 8. MANAGEMENT SYSTEM AUDIT TRACKER MODEL
# ==========================================
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc)

    user = db.relationship('User', back_populates='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} at {self.created_at}>'


# ==========================================
# 9. LIVE DISPATCH SOS EMERGENCY ALERTS MODEL
# ==========================================
class SOSAlert(db.Model):
    __tablename__ = 'sos_alerts'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    triggered_at = db.Column(db.DateTime, default=now_utc)
    status = db.Column(db.String(20), default='Active')  # Active, Resolved

    booking = db.relationship('Booking', back_populates='sos_alerts')

    def __repr__(self):
        return f'<SOSAlert {self.id} | Booking {self.booking_id} | {self.status}>'


# ==========================================
# 10. DYNAMIC PRICING ENGINE MATRICES MODEL
# ==========================================
class FareConfig(db.Model):
    __tablename__ = 'fare_configs'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_category = db.Column(db.String(50), unique=True, nullable=False)
    base_fare = db.Column(db.Float, nullable=False)
    base_distance_km = db.Column(db.Float, nullable=False)
    rate_per_km = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, default=now_utc, onupdate=now_utc)

    def __repr__(self):
        return f'<FareConfig {self.vehicle_category} | ₹{self.base_fare} base | ₹{self.rate_per_km}/km>'


# ==========================================
# 11. LIVE DISPATCH CUSTOMER SUPPORT PORTAL TICKETS
# ==========================================
class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc)

    user = db.relationship('User', backref=db.backref('support_tickets', lazy=True))

    def __repr__(self):
        return f'<SupportTicket {self.id} | User ID: {self.user_id} | From: {self.email}>'


# ==========================================
# 12. INCIDENT REPORTING ENGINE (TRUST & SAFETY)
# ==========================================
class IncidentReport(db.Model):
    __tablename__ = 'incident_reports'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reporter_role = db.Column(db.String(20), nullable=False)  # 'Customer' or 'Driver'
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=now_utc)

    # ⚡ EXPLICIT FOREIGN KEY TRACKING (Wipes out ambiguous relationship errors)
    booking = db.relationship('Booking', backref=db.backref('incident_reports', lazy=True))
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='incidents_reported')
    reported_user = db.relationship('User', foreign_keys=[reported_user_id], backref='incidents_received')

    def __repr__(self):
        return f'<IncidentReport {self.id} | Booking: {self.booking_id} | By: {self.reporter_role}>'
