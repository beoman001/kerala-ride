# 1. MUST BE AT THE ABSOLUTE TOP OF THE FILE BEFORE ANY OTHER IMPORTS
from gevent import monkey
monkey.patch_all()

# 2. Now import the rest of your environment variables and components
import os
from kerala_ride import create_app, socketio, seed_database, celery_app, db
from kerala_ride.models import User

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
    
    # Build your clean presentation master admin account
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

    # Seed fresh demo datasets safely
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
