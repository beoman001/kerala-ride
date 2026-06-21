# 1. MUST BE AT THE ABSOLUTE TOP OF THE FILE BEFORE ANY OTHER IMPORTS
from gevent import monkey
monkey.patch_all()

# 2. Now import the rest of your environment variables and components
import os
from kerala_ride import create_app, socketio, seed_database, celery_app, db
from kerala_ride.models import User

app = create_app()

if __name__ == '__main__':
    # Seed database automatically on launch for a seamless out-of-the-box demo
    seed_database(app)

    # ⚡ CRITICAL ENFORCEMENT: Automatically sync structural updates on Render startup
    with app.app_context():
        # Safely adds missing tables/columns without throwing drops
        db.create_all()
        
        # Auto-seed the presentation admin if missing from the active engine context
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
            print("🚀 Master admin injected into the cloud database cleanly.")

    # DYNAMIC RENDER PORT BINDING FIX
    # Render assigns a dynamic port. If not found, it defaults to 5000 locally.
    port = int(os.environ.get("PORT", 5000))

    print(f"KeralaRide Connect starting on public interface port {port}")
    
    # Use socketio.run but swap out the hardcoded port for our dynamic port variable!
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
