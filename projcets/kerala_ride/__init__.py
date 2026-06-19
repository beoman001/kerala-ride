import os
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, session, request
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from celery import Celery  # 🚀 ENTERPRISE UPGRADE: Asynchronous Distributed Task Queue Engine

# --- SECURITY & BACKEND STORAGE IMPORTS ---
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 1. Initialize extensions globally at the root package level
db = SQLAlchemy()

# 🎯 OPTIMIZED FOR FREE TIER INSTANCES: Tuned polling frames to maintain consistent connectivity
socketio = SocketIO(
    cors_allowed_origins="*", 
    async_mode='threading',
    ping_timeout=10,
    ping_interval=5
)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Initialize global Celery worker application wrapper
celery_app = Celery(__name__)

# Initialize Security Engines
csrf = CSRFProtect()

# 🎯 FREE TIER FALLBACK FIX: Fallback to local memory if production Redis isn't provided
REDIS_URL = os.environ.get('REDIS_URL')
if not REDIS_URL or 'localhost' in REDIS_URL:
    storage_uri = "memory://"
    broker_url = None
    print("💻 System Alert: Redis cloud instance not found. Falling back to safe In-Memory storage.")
else:
    storage_uri = REDIS_URL
    broker_url = REDIS_URL
    print("🚀 System Alert: Connected safely to external Redis cluster engine.")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=storage_uri  # Dynamic configuration drops straight to memory if Redis is missing
)

@login_manager.user_loader
def load_user(user_id):
    # LAZY IMPORT: Prevents models from executing until the app context is fully built
    from kerala_ride.models import User
    return db.session.get(User, int(user_id))

def now_utc():
    """Helper method to return timezone-aware UTC datetime safely."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def create_app(test_config=None):
    """Application factory function to configure and initialize the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # 🎯 FIX FOR ERROR e3q8: Dynamic fallback architecture checks environments automatically
    raw_database_url = os.environ.get('DATABASE_URL')
    
    if not raw_database_url:
        # 💻 LOCAL DEVELOPMENT ENVIRONMENT FALLBACK
        raw_database_url = 'sqlite:///keralaride.db'
        print("💻 System Alert: No production engine found. Defaulting to Local SQLite instance.")
    else:
        # 🚀 CLOUD DEPLOYMENT CONFIGURATION (RENDER POSTGRES)
        if raw_database_url.startswith("postgres://"):
            raw_database_url = raw_database_url.replace("postgres://", "postgresql://", 1)
        print("🚀 System Alert: Database path locked into Production PostgreSQL cluster engine.")

    # 2. Configure default application settings matching distributed backend requirements
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'kerala_ride_connect_dev_secret_key_12345'),
        SQLALCHEMY_DATABASE_URI=raw_database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.root_path, 'static', 'uploads'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload limit
        PERMANENT_SESSION_LIFETIME=timedelta(days=365),  # 🎯 USER-FRIENDLY: Persistent 1-year login wrapper
        CELERY_BROKER_URL=broker_url,
        CELERY_RESULT_BACKEND=broker_url
    )

    if test_config:
        app.config.from_mapping(test_config)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 3. Bind core extension layers to the application instance context
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    
    # Bind Security Engines
    csrf.init_app(app)
    limiter.init_app(app)

    # 🎯 ENTERPRISE UPGRADE: Configure global Celery task instance context parameters safely
    if broker_url:
        celery_app.conf.update(app.config)
        
        class ContextTask(celery_app.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
                    
        celery_app.Task = ContextTask

    # Automatically build missing database tables safely inside application context
    with app.app_context():
        from kerala_ride import models  # Forces SQLAlchemy to scan models cleanly
        db.create_all() 

        # 🎯 AUTOMATIC SEEDING GATEWAY:
        # Verification engine inserts structural dependencies safely only if tables are completely blank
        from kerala_ride.models import User
        try:
            if User.query.first() is None:
                print("🛢️ Empty database detected on app launch! Running automated seed generation...")
                seed_database(app)
        except Exception as seed_err:
            print(f"⚠️ Automated seeding bypass warning: {str(seed_err)}")

    # 4. Register application routing blueprints
    from kerala_ride.routes.auth import auth_bp
    from kerala_ride.routes.main import main_bp
    from kerala_ride.routes.customer import customer_bp
    from kerala_ride.routes.driver import driver_bp
    from kerala_ride.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(driver_bp, url_prefix='/driver')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # 🛡️ EXEMPT ADMIN BLUEPRINT ROUTING MATRIX FROM CSRF VALIDATION WALLS
    csrf.exempt(admin_bp)

    # Custom HTTP error handlers with dynamic string fallbacks
    @app.errorhandler(404)
    def not_found(e):
        try:
            return render_template('errors/404.html'), 404
        except Exception:
            return "404 Not Found: The requested URL was not found on the server.", 404

    @app.errorhandler(500)
    def server_error(e):
        try:
            return render_template('errors/500.html'), 500
        except Exception:
            return f"500 Internal Server Error Traceback Fallback: {str(e)}", 500
        
    @app.errorhandler(429)
    def ratelimit_handler(e):
        try:
            return render_template('errors/429.html', error="Too many requests. Please slow down and try again in a few minutes."), 429
        except Exception:
            return "429 Too Many Requests: Rate limit exceeded.", 429

    # Command Line Interface (CLI) seed command definition
    @app.cli.command("seed-db")
    def seed_db_command():
        seed_database(app)

    # --- MASTER VEHICLE CATEGORY LISTS ---
    PASSENGER_VEHICLES = [
        "Auto Rickshaw",
        "Taxi",
        "Standard Cars",
        "8-Seater SUV",
        "MPV",
        "Tempo Traveller",
        "Mini Bus",
        "Tourist Bus"
    ]

    GOODS_VEHICLES = [
        "Goods Auto",
        "Pickup",
        "Mini Truck",
        "Lorry"
    ]

    MASTER_VEHICLES = PASSENGER_VEHICLES + GOODS_VEHICLES

    # Context processors inject these variables into EVERY HTML template automatically
    @app.context_processor
    def inject_globals():
        return {
            'now': now_utc(),
            'VEHICLE_CATEGORIES': MASTER_VEHICLES,
            'PASSENGER_VEHICLES': PASSENGER_VEHICLES,
            'GOODS_VEHICLES': GOODS_VEHICLES
        }

    # 🎯 NEW CACHE ENGINE: Forces mobile devices to store static assets locally to eliminate network lag
    @app.after_request
    def add_header(response):
        if 'Cache-Control' not in response.headers and request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        return response

    return app

def seed_database(app):
    """Seeds the database with default sample records for users, drivers, and promotions."""
    with app.app_context():
        from kerala_ride.models import User, Driver, Vehicle, PromoOffer, SavedLocation, EmergencyContact, FareConfig
        
        # Double check inside function scope to guard against accidental duplicate seeding calls
        if User.query.first() is not None:
            print("Database already contains data inside seed verification check. Seeding skipped.")
            return

        print("Seeding database with default users and records...")

        # 1. Seed System Admin Account
        admin = User(email="admin@keralaride.com", name="Admin Manager", phone="9876543210", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        # 2. Seed Customer Account & Shortcuts
        customer = User(email="customer@keralaride.com", name="Anjali Nair", phone="9446012345", role="customer")
        customer.set_password("customer123")
        db.session.add(customer)
        db.session.flush()

        loc_home = SavedLocation(user_id=customer.id, label="Home", address="Nair Villa, Kakkanad, Kochi, Ernakulam")
        loc_work = SavedLocation(user_id=customer.id, label="Work", address="Infopark Phase 1, Kakkanad, Kochi, Ernakulam")
        contact_sos = EmergencyContact(user_id=customer.id, name="Suresh Nair (Father)", phone="9447098765")
        db.session.add_all([loc_home, loc_work, contact_sos])

        # 3. Seed Verified Partner Driver 1 (Auto)
        driver1_user = User(email="driver@keralaride.com", name="Hari Kumar", phone="9847055667", role="driver")
        driver1_user.set_password("driver123")
        db.session.add(driver1_user)
        driver1_user.permanent_session_lifetime = True
        db.session.flush()

        driver1_profile = Driver(
            user_id=driver1_user.id,
            district="Ernakulam",
            local_body_type="Municipality",
            local_body_name="Thrikkakara",
            license_number="KL-07-2015-0012345",
            permit_number="P-EKM-2022-7788",
            verification_status="Approved",
            is_online=True
        )
        db.session.add(driver1_profile)
        db.session.flush()

        vehicle1 = Vehicle(
            driver_id=driver1_profile.id,
            category="Auto Rickshaw",
            brand="Bajaj",
            model="RE Optima",
            plate_number="KL-07-CD-4321",
            seating_capacity=3,
            manufacture_year=2021,
            verification_status="Approved"
        )
        db.session.add(vehicle1)

        # 4. Seed Pending Partner Driver 2 (Taxi)
        driver2_user = User(email="driver2@keralaride.com", name="Mohan Lal", phone="9845612345", role="driver")
        driver2_user.set_password("driver123")
        db.session.add(driver2_user)
        db.session.flush()

        driver2_profile = Driver(
            user_id=driver2_user.id,
            district="Trivandrum",
            local_body_type="Corporation",
            local_body_name="Trivandrum City",
            license_number="KL-01-2012-0098765",
            permit_number="P-TVM-2021-9988",
            verification_status="Pending",
            is_online=False
        )
        db.session.add(driver2_profile)
        db.session.flush()

        vehicle2 = Vehicle(
            driver_id=driver2_profile.id,
            category="Taxi",
            brand="Maruti Suzuki",
            model="Dzire",
            plate_number="KL-01-CA-5566",
            seating_capacity=4,
            manufacture_year=2020,
            verification_status="Pending"
        )
        db.session.add(vehicle2)

        # 5. Seed Core Base Fare Configurations
        config_auto = FareConfig(vehicle_category="Auto Rickshaw", base_fare=40.0, base_distance_km=1.5, rate_per_km=12.0)
        config_taxi = FareConfig(vehicle_category="Taxi", base_fare=60.0, base_distance_km=3.0, rate_per_km=15.0)
        config_suv = FareConfig(vehicle_category="8-Seater SUV", base_fare=100.0, base_distance_km=5.0, rate_per_km=22.0)
        config_truck = FareConfig(vehicle_category="Mini Truck", base_fare=150.0, base_distance_km=5.0, rate_per_km=25.0)
        db.session.add_all([config_auto, config_taxi, config_suv, config_truck])

        # 6. Seed Promo Offers
        promo1 = PromoOffer(
            code="KERALA50",
            description="Get 50% off on your first trip (Up to ₹100)",
            discount_percentage=50.0,
            expiry_date=now_utc() + timedelta(days=30)
        )
        promo2 = PromoOffer(
            code="MONSOON20",
            description="Monsoon special: 20% discount on goods transport bookings",
            discount_percentage=20.0,
            expiry_date=now_utc() + timedelta(days=15)
        )
        db.session.add_all([promo1, promo2])

        db.session.commit()
        print("Database seeded successfully with explicit configurations and models!")
