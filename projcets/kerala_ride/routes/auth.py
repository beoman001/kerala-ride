import os
import re
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

# Import the rate limiter from your main app initialization
from kerala_ride import limiter 
from kerala_ride.models import db, User, Driver, Vehicle

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, driver_id, doc_type):
    if not file or file.filename == '':
        return None
    if allowed_file(file.filename):
        # Secure the original filename to prevent directory traversal attacks
        safe_filename = secure_filename(file.filename)
        driver_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'driver_{driver_id}')
        os.makedirs(driver_dir, exist_ok=True)
        
        ext = safe_filename.rsplit('.', 1)[1].lower()
        # Rename to a standard format so files don't overwrite each other randomly
        new_filename = f"{doc_type}_{driver_id}.{ext}"
        file.save(os.path.join(driver_dir, new_filename))
        
        return f"uploads/driver_{driver_id}/{new_filename}"
    return None


def clean_phone_number(phone_str):
    """
    🧹 Phone Standardization Engine:
    Removes non-numeric decorations and standardizes local formats for SMS Gateways.
    """
    if not phone_str:
        return ""
    # Strip spaces, brackets, dashes, and letters
    cleaned = re.sub(r'\D', '', phone_str)
    
    # If it has a prefixed 91 and is 12 digits long, strip the 91 so it stores purely as a 10-digit base number
    if len(cleaned) == 12 and cleaned.startswith('91'):
        cleaned = cleaned[2:]
        
    return cleaned


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute") # 🛡️ Blocks brute-force password guessing
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'driver':
            return redirect(url_for('driver.dashboard'))
        return redirect(url_for('customer.dashboard'))

    if request.method == 'POST':
        # .lower() ensures case-insensitivity so mobile users don't get locked out by Auto-Caps
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        # Find user and securely check the full 255-character hash
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)

        # 🎯 FIX: Route user to their exact dashboard matching admin.py endpoints
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'driver':
            driver_profile = Driver.query.filter_by(user_id=user.id).first()
            if driver_profile and driver_profile.verification_status != 'Approved':
                flash(f"Your driver account is currently: {driver_profile.verification_status}. You'll have restricted access until approved.", "warning")
            return redirect(url_for('driver.dashboard'))
        
        return redirect(url_for('customer.dashboard'))

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute") # 🛡️ Stops bot spam account creation
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        phone = clean_phone_number(request.form.get('phone', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(phone) != 10:
            flash('Please enter a valid 10-digit mobile number.', 'danger')
            return redirect(url_for('auth.register'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.register'))
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('That email address is already registered.', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(email=email, name=name, phone=phone, role='customer')
        new_user.set_password(password) # This now safely generates the sha256 hash
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/driver-register', methods=['GET', 'POST'])
@limiter.limit("3 per minute") # 🛡️ Stops fake driver apps & malicious file uploads
def driver_register():
    if current_user.is_authenticated and current_user.role != 'driver':
        flash('Please log out first to apply as a driver.', 'warning')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        phone = clean_phone_number(request.form.get('phone', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(phone) != 10:
            flash('Please enter a valid 10-digit mobile number for dispatch alerts.', 'danger')
            return redirect(url_for('auth.driver_register'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.driver_register'))
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.driver_register'))
        if User.query.filter_by(email=email).first():
            flash('That email address is already registered.', 'danger')
            return redirect(url_for('auth.driver_register'))

        new_user = User(email=email, name=name, phone=phone, role='driver')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        new_driver = Driver(
            user_id=new_user.id,
            district=request.form.get('district', ''),
            local_body_type=request.form.get('local_body_type', ''),
            local_body_name=request.form.get('local_body_name', ''),
            license_number=request.form.get('license_number', ''),
            permit_number=request.form.get('permit_number', ''),
            verification_status='Pending'
        )
        db.session.add(new_driver)
        db.session.flush()

        # Handle document uploads safely
        new_driver.photo_path = save_uploaded_file(request.files.get('photo'), new_driver.id, 'photo')
        new_driver.license_path = save_uploaded_file(request.files.get('license'), new_driver.id, 'license')
        new_driver.rc_path = save_uploaded_file(request.files.get('rc'), new_driver.id, 'rc')
        new_driver.permit_path = save_uploaded_file(request.files.get('permit'), new_driver.id, 'permit')
        new_driver.insurance_path = save_uploaded_file(request.files.get('insurance'), new_driver.id, 'insurance')
        new_driver.pollution_path = save_uploaded_file(request.files.get('pollution'), new_driver.id, 'pollution')
        new_driver.yellow_board_photo_path = save_uploaded_file(request.files.get('yellow_board_photo'), new_driver.id, 'yellow_board')
        new_driver.vehicle_images_path = save_uploaded_file(request.files.get('vehicle_images'), new_driver.id, 'vehicle_img')

        new_vehicle = Vehicle(
            driver_id=new_driver.id,
            category=request.form.get('vehicle_category', ''),
            brand=request.form.get('vehicle_brand', ''),
            model=request.form.get('vehicle_model', ''),
            plate_number=request.form.get('plate_number', ''),
            seating_capacity=request.form.get('seating_capacity', type=int, default=4),
            manufacture_year=request.form.get('manufacture_year', type=int, default=2020),
            verification_status='Pending'
        )
        db.session.add(new_vehicle)
        db.session.commit()

        flash('Driver registration submitted! An administrator will review your documents shortly.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('driver_register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))
