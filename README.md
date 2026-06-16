# KeralaRide Connect 🚗📦

A production-ready, highly responsive web application designed for seamless on-demand passenger transport and localized goods cargo transit. Built entirely using robust open-source tools, this platform completely eliminates the dependency on expensive, restrictive paid mapping APIs by leveraging free, high-performance interactive OpenStreetMap components.

---

## 🚀 Key Features

* **Dual-Service Mode Engine:** Intuitive tab-switching UI allowing users to easily pivot between booking **Passenger Rides** or orchestrating **Goods Cargo Logistics**.
* **Touch-Optimized Map Canvas:** Embedded maps powered by Leaflet.js running CartoDB Voyager tiles. It features automatic client-side GPS location tracking, precise pin-dropping, and native touch gesture support on mobile devices.
* **On-Road Route Geometry Vectoring:** Directly communicates with the open-source OSRM engine using a `geojson` fallback to draw hyper-accurate driving route paths wrapping cleanly around street segments.
* **Dynamic Multi-Tiered Fare Configuration:** Automatically pulls specific baseline rules from a structured database (or fallbacks) to compute pricing based on vehicle dimensions, weight limits, base distances, and extra kilometer thresholds.
* **Automated Dual-Zone Return Charges:** Implements a strict dual-zone fallback logic to secure driver compensation:
  * **Short/Local Trips (≤ 500 km):** Automatically adds an identical return charge matching the forward route calculation (effectively generating a clean 2x total rate).
  * **Outstation Long Hauls (> 500 km):** Drops the flat localized minimum base rate for the return trip, charging exclusively for the return journey via flat distance multiplied by the vehicle’s explicit per-kilometer rate.
* **15-Minute Grace Period Cancellation Loop:** Protects driver time and resources. Passengers can cancel requests unconditionally within a 15-minute window. Cancellations executed after 15 minutes automatically incur a structured 1/4th (25%) penalty fee attached to their profile.
* **Anti-Spam Form Double-Booking Guard:** Front-end JavaScript lock instantly disables submission handlers upon click to prevent database congestion from repeated button clicks on slow networks.

---

## 🛠️ Technology Stack

* **Backend Environment:** Python 3.x / Flask Framework
* **Database & Persistence:** Flask-SQLAlchemy (SQLite for development / PostgreSQL compatible)
* **Session & Authentication Control:** Flask-Login Security Stack
* **Frontend Architecture:** HTML5, CSS3 Grid Layouts, Bootstrap 5, FontAwesome Icons
* **Mapping Engine Integration:** Leaflet.js API, Photon Geocoding Engine (Komoot), OSRM Routing Machine

---

## 📦 File Architecture

```text
kerala-ride-connect/
│
├── Procfile             # Production process manager for deployment
├── requirements.txt     # Locked application dependencies 
├── run.py               # Application startup entry-point script
│
└── kerala_ride/         # Core application codebase folder
    ├── __init__.py      # Flask application initialization factory
    ├── models.py        # Database entity models (User, Booking, FareConfig)
    ├── templates/       # HTML template directories
    │   └── customer/
    │       ├── book.html       # Interactive booking template map window
    │       └── dashboard.html  # Live tracking & historical status panel
    └── routes/
        └── customer.py  # Fare computation, cancellation management, and APIs

