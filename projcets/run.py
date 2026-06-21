# 1. MUST BE AT THE ABSOLUTE TOP OF THE FILE BEFORE ANY OTHER IMPORTS
from gevent import monkey
monkey.patch_all()

# 2. Now import the rest of your environment variables and components
import os
from kerala_ride import create_app, socketio, seed_database, celery_app, db
from kerala_ride.models import User

app = create_app()

if __name__ == '__main__':
    # ⚡ FORCE DATABASE STRUCTURAL REBUILD
    with app.app_context():
        print("⚠️ Dropping old outdated table structures...")
        db.drop_all() 
        
        print("✨ Creating brand new synchronized layout schemas...")
        db.create_all() 
        
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
            print("🚀 Master admin freshly initialized.")

    # Seed fresh demo datasets safely now that columns line up perfectly
    seed_database(app)

    # DYNAMIC RENDER PORT BINDING FIX
    port = int(os.environ.get("PORT", 5000))
    print(f"KeralaRide Connect starting on public interface port {port}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
