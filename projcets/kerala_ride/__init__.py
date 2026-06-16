import os
from datetime import datetime, timedelta
from flask import Flask, render_template, session
from flask_login import LoginManager
from flask_socketio import SocketIO
from kerala_ride.models import db, User, Driver, Vehicle, PromoOffer, SavedLocation, EmergencyContact, FareConfig

# 1. Initialize external extensions
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    """Callback used to reload the user object from the user ID stored in the session."""
    return db.session.get(User, int(user_id))


def now_utc():
    """Helper method to return timezone-naive UTC datetime safely."""
    return datetime.utcnow()


def create_app(test_config=None):
    """Application factory function to configure and initialize the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # 2. Configure default application settings
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'kerala_ride_connect_dev_secret_key_12345'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///keralaride.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.root_path, 'static', 'uploads'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload limit
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)  # Strict auto-logout timeout
    )

    if test_config:
        app.config.from_mapping(test_config)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # 3. Bind extensions to the application instance
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    # Automatically build missing database tables upon initialization
    with app.app_context():
        db.create_all()

    # --- SECURITY: Force session to use the strict 30-min timeout timer ---
    @app.before_request
    def make_session_permanent():
        session.permanent = True

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

    # Custom HTTP error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # Command Line Interface (CLI) seed command definition
    @app.cli.command("seed-db")
    def seed_db_command():
        seed_database(app)

    # --- MASTER VEHICLE CATEGORY LISTS ---
    # These lists dictate what shows up in the dropdowns for customers, drivers, and admins
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

    return app


def seed_database(app):
    """Seeds the database with default sample records for users, drivers, and promotions."""
    with app.app_context():
        db.create_all()

        if User.query.first() is not None:
            print("Database already contains data. Seeding skipped.")
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
        loc_work = SavedLocation(user_id=customer.id, label="Work",
                                 address="Infopark Phase 1, Kakkanad, Kochi, Ernakulam")
        contact_sos = EmergencyContact(user_id=customer.id, name="Suresh Nair (Father)", phone="9447098765")
        db.session.add_all([loc_home, loc_work, contact_sos])

        # 3. Seed Verified Partner Driver 1
        driver1_user = User(email="driver@keralaride.com", name="Hari Kumar", phone="9847055667", role="driver")
        driver1_user.set_password("driver123")
        db.session.add(driver1_user)
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

        # 4. Seed Pending Partner Driver 2
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

        # 5. Seed Promo Offers
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
        print("Database seeded successfully with users and dynamic rules!")