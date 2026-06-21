// KeralaRide Connect SocketIO Event Router & Production Dispatch Engine
document.addEventListener("DOMContentLoaded", function() {
    // Establish connection to socket server
    const socket = io();
    let realDriverMarkers = {}; // Cache to track live driver layer markers by ID

    socket.on('connect', () => {
        console.log('Connected to KeralaRide Connect WebSocket server.');
        // Register passenger room state inside backend pool tower
        socket.emit('join_passenger_pool', {});
    });

    // Automatically resolve any dimensional tile bugs on initialization
    if (typeof map !== 'undefined' && map) {
        setTimeout(() => { map.invalidateSize(); }, 400);
    }

    // ==========================================================================
    // ⚡ REGION 1: LIVE BROADCAST FLEET MAPPING (REPLACES MOCK MATH LOOPS)
    // ==========================================================================
    socket.on('fleet_coordinates_broadcast', (data) => {
        // Intercepts active driver coordinates emitted from the WebSocket server tower
        const { driver_id, lat, lng, vehicle_tier } = data;
        
        // Ensure our global Leaflet map instance is fully operational on the page
        if (typeof map !== 'undefined' && map) {
            
            // If vehicle tier matches our currently selected filter or if map is idle
            const driverIconHtml = `
                <div style="background:#064e3b; width:28px; height:28px; border-radius:50%; border:2px solid white; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,0.3); transition: transform 0.4s linear;">
                    <i class="fa-solid fa-car" style="color:white; font-size:12px;"></i>
                </div>`;
            
            const cabIcon = L.divIcon({ className: 'cab-marker-node', html: driverIconHtml, iconSize: [28, 28] });

            if (realDriverMarkers[driver_id]) {
                // Update position smoothly over web-canvas without layout thrashing
                realDriverMarkers[driver_id].setLatLng([lat, lng]);
            } else {
                // Instantly generate new marker layer nodes for freshly connected vehicles
                realDriverMarkers[driver_id] = L.marker([lat, lng], { icon: cabIcon }).addTo(map);
            }
        }
    });

    // ==========================================================================
    // ⚡ REGION 2: MULTI-STOP COMPATIBLE TRADITIONAL FORM PASS-THROUGH ROUTING
    // ==========================================================================
    const formBookBtn = document.getElementById("bookBtn");
    if (formBookBtn) {
        // Intercept click to check presence of basic coordinates and active stopovers
        formBookBtn.addEventListener("click", function(e) {
            const pickup = document.getElementById("pickup").value.trim();
            const destination = document.getElementById("destination").value.trim();
            const p_lat = document.getElementById("pickup_lat").value;
            const d_lat = document.getElementById("dest_lat").value;

            // ⚡ HARDENED: Conditionally check stopover requirements if field is visible
            const stopoverCol = document.getElementById("stopoverContainerCol");
            const isStopoverActive = stopoverCol && !stopoverCol.classList.contains("strictly-hidden");
            
            if (isStopoverActive) {
                const stopover = document.getElementById("stopover").value.trim();
                const s_lat = document.getElementById("stopover_lat").value;
                
                if (!stopover || !s_lat) {
                    e.preventDefault();
                    alert("Please specify your stopover point layout parameters completely or clear the stop field before booking!");
                    return false;
                }
            }

            if (!pickup || !destination || !p_lat || !d_lat) {
                e.preventDefault(); // Halt submission if mapping targets are empty
                alert("Please make sure you specify base locations and map parameters completely before booking!");
                return false;
            }

            console.log("🚀 Form validation criteria cleared. Dispatching multi-stop form context lines directly to Python.");
        });
    }

    // ==========================================================================
    // ⚡ REGION 3: SIGNAL NOTIFICATION EVENT LISTENERS
    // ==========================================================================
    // 1. Customer Trip Updates Listener
    socket.on('booking_status', (data) => {
        const activeTripCard = document.getElementById(`trip-card-${data.booking_id}`);
        if (activeTripCard) {
            console.log("Trip status change received:", data);
            
            // If the status is completed, reload the page to display final fare details and receipt
            if (data.status === 'Completed') {
                window.location.reload();
                return;
            }
            
            // Otherwise, update UI indicators
            const statusBadge = activeTripCard.querySelector(".badge");
            if (statusBadge) {
                statusBadge.className = `badge badge-${data.status.toLowerCase()}`;
                statusBadge.innerText = data.status;
            }

            const statusText = document.getElementById("trip-status-text");
            if (statusText) {
                if (data.status === 'Accepted') statusText.innerText = "Driver Assigned & En Route";
                else if (data.status === 'Arrived') statusText.innerText = "Driver Arrived at Pickup";
                else if (data.status === 'Active') statusText.innerText = "Trip in Progress";
            }

            // Update Map Tracker if available
            if (window.mapTrackerInstance) {
                window.mapTrackerInstance.updateStatus(data.status);
            }
            
            // Reload page on major milestones to refresh driver detail blocks
            if (data.status === 'Accepted' || data.status === 'Active') {
                setTimeout(() => window.location.reload(), 1500);
            }
        }
    });

    // 2. Online Driver Booking Dispatcher
    socket.on('new_booking', (data) => {
        const driverDashboard = document.getElementById('driver-dashboard-console');
        if (driverDashboard) {
            console.log("New booking dispatch received:", data);
            
            // Create a sliding booking alert box at the bottom right
            // Remove existing alert if present
            const oldAlert = document.getElementById('booking-dispatch-popup');
            if (oldAlert) oldAlert.remove();

            const popup = document.createElement('div');
            popup.id = 'booking-dispatch-popup';
            popup.className = 'card glass-card booking-popup-modal';
            
            let goodsMeta = '';
            if (data.type === 'goods') {
                goodsMeta = `
                    <div style="margin: 8px 0; font-size: 13px; color: #4b5563;">
                        <strong>Goods Description:</strong> ${data.material} <br>
                        <strong>Weight:</strong> ${data.weight} kg
                    </div>
                `;
            }

            // ⚡ EXTRA: Display stopover metadata if provided in the dynamic stream
            let stopoverMeta = '';
            if (data.stopover) {
                stopoverMeta = `<p style="font-size: 13px; color: #b45309;"><strong>Stopover:</strong> ${data.stopover}</p>`;
            }

            popup.innerHTML = `
                <div class="card-title" style="border-bottom: 2px solid var(--primary-color); color: var(--primary-color);">
                    <span>⚡ New Booking Request</span>
                    <span class="badge badge-active">${data.type}</span>
                </div>
                <div style="margin-bottom: 15px;">
                    <p style="font-size: 15px; margin-bottom: 4px;"><strong>Customer:</strong> ${data.customer_name}</p>
                    <p style="font-size: 13px; color: #4b5563;"><strong>Pickup:</strong> ${data.pickup}</p>
                    ${stopoverMeta}
                    <p style="font-size: 13px; color: #4b5563;"><strong>Drop:</strong> ${data.destination}</p>
                    ${goodsMeta}
                    <h3 style="color: var(--accent-amber); margin-top: 10px;">Est. Fare: ₹${data.fare}</h3>
                </div>
                <div style="display: flex; gap: 10px;">
                    <form action="/driver/accept/${data.booking_id}" method="POST" style="flex: 1;">
                        <button type="submit" class="btn btn-primary btn-sm" style="width: 100%;">Accept Job</button>
                    </form>
                    <button onclick="document.getElementById('booking-dispatch-popup').remove();" class="btn btn-outline btn-sm" style="flex: 1;">Ignore</button>
                </div>
            `;

            document.body.appendChild(popup);
            
            // Auto close after 30 seconds
            setTimeout(() => {
                const popupToClose = document.getElementById('booking-dispatch-popup');
                if (popupToClose) popupToClose.remove();
            }, 30000);
        }
    });

    // 3. Admin Emergency SOS Receiver
    socket.on('sos_triggered', (data) => {
        const adminDashboard = document.getElementById('admin-dashboard-console');
        if (adminDashboard) {
            console.log("Emergency SOS Alert received:", data);
            
            // Create a top flashing emergency alert banner
            const sosBanner = document.createElement('div');
            sosBanner.className = 'alert alert-danger';
            sosBanner.style.position = 'fixed';
            sosBanner.style.top = '10px';
            sosBanner.style.left = '50%';
            sosBanner.style.transform = 'translateX(-50%)';
            sosBanner.style.zIndex = '9999';
            sosBanner.style.width = '90%';
            sosBanner.style.maxWidth = '800px';
            sosBanner.style.boxShadow = '0 0 20px rgba(220, 38, 38, 0.8)';
            sosBanner.style.animation = 'pulse 1.5s infinite';
            
            sosBanner.innerHTML = `
                <div style="flex-grow: 1;">
                    <strong>🚨 EMERGENCY SOS ACTIVE</strong> | Customer: ${data.customer_name} (${data.customer_phone}) <br>
                    <strong>Trip:</strong> ${data.pickup} to ${data.destination} <br>
                    <strong>Coordinates:</strong> Lat ${data.latitude}, Lng ${data.longitude} | <strong>Driver:</strong> ${data.driver_name} (${data.driver_phone})
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <button onclick="window.location.reload();" class="btn btn-sm btn-primary">Refresh Console</button>
                    <span class="alert-close">&times;</span>
                </div>
            `;
            
            document.body.appendChild(sosBanner);
            
            // Handle alert dismiss
            sosBanner.querySelector('.alert-close').addEventListener('click', function() {
                sosBanner.remove();
            });
        }
    });
});
