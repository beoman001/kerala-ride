# 1. MUST BE AT THE ABSOLUTE TOP OF THE FILE BEFORE ANY OTHER IMPORTS
from gevent import monkey
monkey.patch_all()

# 2. Now import the rest of your environment variables and components
import os
from kerala_ride import create_app, socketio, seed_database, celery_app, db
from kerala_ride.models import User, Driver

app = create_app()

# ==============================================================================
# ⚡ PRODUCTION BOOTSTRAP ENGINE (Bypasses Gunicorn's __main__ block trap)
# ==============================================================================
with app.app_context():
    print("⚠️ [SYSTEM] Initiating Database Schema Synchronization...")
    
    # Drops the corrupted tables that are causing the 500 Internal Error
    db.drop_all() 
    print("🗑️ [SYSTEM] Old corrupted tables dropped.")
    
    # Rebuilds the tables with the brand new stopover_location columns
    db.create_all()
    print("✨ [SYSTEM] Brand new synchronized layout schemas created.")
    
    # ---------------------------------------------------------
    # 1. Build your clean presentation Master Admin account
    # ---------------------------------------------------------
    admin_exists = User.query.filter_by(email="admin@keralaride.com").first()
    if not admin_exists:
        master_admin = User(
            name="System Admin",
            email="admin@keralaride.com",
            phone="9999999999",
            role="Admin"
        )
        master_admin.set_password("AdminTest2026!")
        db.session.add(master_admin)
        db.session.commit()
        print("🚀 [SYSTEM] Master admin freshly initialized.")

    # ---------------------------------------------------------
    # 2. Build your guaranteed Test Driver account
    # ---------------------------------------------------------
    driver_exists = User.query.filter_by(email="driver@keralaride.com").first()
    if not driver_exists:
        test_driver_user = User(
            name="Test Driver",
            email="driver@keralaride.com",
            phone="8888888888",
            role="driver"
        )
        test_driver_user.set_password("driver123") # Set exactly to driver123
        db.session.add(test_driver_user)
        db.session.flush() # Flush gets the ID before committing
        
        # ⚡ FIXED: Added all mandatory fields to satisfy PostgreSQL NOT NULL constraints
        test_driver_profile = Driver(
            user_id=test_driver_user.id,
            district="Ernakulam",
            local_body_type="Corporation",       # Satisfies NOT NULL constraint
            local_body_name="Kochi",             # Satisfies NOT NULL constraint
            license_number="KL-07-2026-0004321", # Satisfies NOT NULL constraint
            permit_number="P-COMM-2026-X",       # Satisfies NOT NULL constraint
            verification_status="Approved",
            is_online=True
        )
        db.session.add(test_driver_profile)
        db.session.commit()
        print("🚖 [SYSTEM] Test Driver freshly initialized with full schema compliance.")

    # ---------------------------------------------------------
    # 3. Seed fresh demo datasets safely
    # ---------------------------------------------------------
    try:
        seed_database(app)
        print("🌱 [SYSTEM] Demo datasets seeded successfully.")
    except Exception as e:
        print(f"⚠️ [SYSTEM] Seeding warning bypassed: {e}")


# ==============================================================================
# 🚀 LOCAL DEVELOPMENT LAUNCHER
# ==============================================================================
if __name__ == '__main__':
    # DYNAMIC RENDER PORT BINDING FIX
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 KeralaRide Connect starting on public interface port {port}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
