import os
from kerala_ride import create_app, socketio, seed_database

app = create_app()

if __name__ == '__main__':
    # Seed database automatically on launch for a seamless out-of-the-box demo
    seed_database(app)

    # Run Flask-SocketIO server
    # Note: socketio.run handles the web server and supports real-time notifications
    print("KeralaRide Connect starting on http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
