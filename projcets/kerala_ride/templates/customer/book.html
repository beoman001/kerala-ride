{% extends "base.html" %}

{% block title %}Book a Ride - KeralaRide Connect{% endblock %}

{% block content %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

<style>
    /* Sleek tabs matching reference configurations */
    .nav-tabs-custom {
        display: flex;
        border-bottom: 2px solid #d1d5db;
        margin-bottom: 25px;
        width: 100%;
    }
    .nav-tab-item {
        flex: 1;
        text-align: center;
        padding: 15px;
        cursor: pointer;
        font-weight: 800;
        color: #6b7280;
        font-size: 15px;
        transition: all 0.2s ease-in-out;
        border-bottom: 3px solid transparent;
    }
    .nav-tabs-custom .nav-tab-item.active {
        color: #111827 !important;
        border-bottom: 3px solid #064e3b !important;
    }
    .nav-tab-item:hover:not(.active) {
        background-color: #f9fafb;
        color: #374151;
    }

    /* Subdued input styling */
    .form-control, .form-select {
        background-color: #f3f4f6;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 10px 15px;
        font-size: 14px;
        width: 100%;
    }
    .form-control:focus, .form-select:focus {
        background-color: #ffffff;
        border-color: #064e3b;
        box-shadow: 0 0 0 0.2rem rgba(6, 78, 59, 0.1);
    }
    .form-label {
        font-weight: 700;
        color: #374151;
        font-size: 13px;
        margin-bottom: 6px;
    }

    /* High-Precision Free Map Canvas */
    #map-canvas {
        height: 350px;
        width: 100%;
        margin-bottom: 20px;
        border-radius: 8px;
        border: 1px solid #d1d5db;
        z-index: 1;
    }

    .map-instruction {
        font-size: 12px;
        color: #064e3b;
        background-color: #e6f4ea;
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 15px;
        font-weight: 600;
    }

    /* Custom styling for free search dropdown boxes */
    .autocomplete-container {
        position: relative;
        transition: all 0.2s ease-in-out;
    }
    .suggestions-list {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #d1d5db;
        border-top: none;
        border-radius: 0 0 6px 6px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 9999;
        margin: 0;
        padding: 0;
        list-style: none;
    }
    .suggestions-list li {
        padding: 10px 15px;
        cursor: pointer;
        font-size: 13px;
        border-bottom: 1px solid #f3f4f6;
    }
    .suggestions-list li:hover {
        background-color: #f3f4f6;
    }

    .strictly-hidden {
        display: none !important;
    }

    /* Vehicle Cards Layout */
    .vehicle-cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 15px;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    
    .vehicle-card {
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 14px;
        padding: 14px 18px;
        display: flex;
        align-items: center;
        gap: 15px;
        cursor: pointer;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .vehicle-card:hover {
        border-color: #cbd5e1;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    
    .vehicle-card.selected {
        border-color: #064e3b !important;
        background-color: rgba(6, 78, 59, 0.02);
    }
    
    .vehicle-card.selected::after {
        content: '\f058';
        font-family: 'Font Awesome 6 Free';
        font-weight: 900;
        position: absolute;
        top: 10px;
        right: 12px;
        color: #064e3b;
        font-size: 16px;
    }
    
    .vehicle-card img {
        width: 50px;
        height: 50px;
        object-fit: contain;
    }
    
    .vehicle-info {
        flex: 1;
    }
    
    .vehicle-info h5 {
        margin: 0 0 3px 0;
        font-size: 15px;
        font-weight: 700;
        color: #1f2937;
    }
    
    .vehicle-info p {
        margin: 0;
        font-size: 12px;
        color: #6b7280;
    }
    
    .vehicle-price {
        font-size: 16px;
        font-weight: 800;
        color: #064e3b;
    }
</style>

<div class="container my-5" style="margin-bottom: 80px;">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card shadow-sm border-0" style="border-radius: 12px; background-color: #fdfdfd;">
                <div class="card-body p-4 p-md-5">

                    <div class="nav-tabs-custom" id="serviceTabs">
                        <div class="nav-tab-item active" id="tabPassenger">
                            <i class="fa-solid fa-user-friends me-2"></i> Passenger Ride
                        </div>
                        <div class="nav-tab-item" id="tabGoods">
                            <i class="fa-solid fa-truck-moving me-2"></i> Goods Cargo
                        </div>
                    </div>

                    <div class="map-instruction">
                        <i class="fa-solid fa-map-location-dot me-1"></i> Type to search addresses or <b>tap directly on the map</b> to drop pins anywhere in Kerala!
                    </div>

                    <div id="map-canvas"></div>

                    <form method="POST" action="{{ url_for('customer.book') }}" id="bookingForm">
                        
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                        
                        <input type="hidden" name="booking_type" id="booking_type" value="passenger">
                        <input type="hidden" name="estimated_fare" id="estimated_fare" value="0.0">
                        <input type="hidden" name="pickup_district" id="pickup_district" value="">
                        
                        <input type="hidden" name="pickup_lat" id="pickup_lat" value="">
                        <input type="hidden" name="pickup_lng" id="pickup_lng" value="">
                        <input type="hidden" name="stopover_lat" id="stopover_lat" value="">
                        <input type="hidden" name="stopover_lng" id="stopover_lng" value="">
                        <input type="hidden" name="dest_lat" id="dest_lat" value="">
                        <input type="hidden" name="dest_lng" id="dest_lng" value="">

                        <div class="row mb-2" id="routingInputRow">
                            <div class="col-md-6 mb-3 autocomplete-container" id="pickupContainerCol">
                                <label class="form-label">
                                    <input type="radio" name="map_target" id="target_pickup" value="pickup" checked class="me-1">
                                    Pickup Address <span class="text-danger">*</span>
                                </label>
                                <input type="text" id="pickup" name="pickup" class="form-control" placeholder="Search address or tap map" autocomplete="off" required>
                                <ul id="pickup-suggestions" class="suggestions-list strictly-hidden"></ul>
                            </div>

                            <div class="col-md-4 mb-3 autocomplete-container strictly-hidden" id="stopoverContainerCol">
                                <label class="form-label">
                                    <input type="radio" name="map_target" id="target_stopover" value="stopover" class="me-1">
                                    Stopover Address
                                </label>
                                <div style="display: flex; gap: 6px;">
                                    <input type="text" id="stopover" name="stopover" class="form-control" placeholder="Search stopover or tap map" autocomplete="off">
                                    <button type="button" onclick="removeStopoverField()" class="btn btn-outline-danger" style="padding: 10px 14px;"><i class="fa-solid fa-trash-can"></i></button>
                                </div>
                                <ul id="stopover-suggestions" class="suggestions-list strictly-hidden"></ul>
                            </div>

                            <div class="col-md-6 mb-3 autocomplete-container" id="destContainerCol">
                                <label class="form-label">
                                    <input type="radio" name="map_target" id="target_dest" value="destination" class="me-1">
                                    Destination / Dropoff <span class="text-danger">*</span>
                                </label>
                                <input type="text" id="destination" name="destination" class="form-control" placeholder="Search address or tap map" autocomplete="off" required>
                                <ul id="dest-suggestions" class="suggestions-list strictly-hidden"></ul>
                            </div>
                        </div>

                        <div class="mb-4" id="addStopHudSection">
                            <button type="button" onclick="addStopoverField()" class="btn btn-link p-0 text-success font-weight-bold" style="text-decoration: none; font-size: 13px;">
                                <i class="fa-solid fa-circle-plus me-1"></i> Add a Stopover Point
                            </button>
                        </div>

                        <div class="mb-3 p-3 rounded" style="background-color: #f8fafc; border: 1px solid #e2e8f0;" id="waitingChargeWrapper">
                            <label class="form-label" for="waiting_minutes"><i class="fa-regular fa-clock me-1 text-secondary"></i> Schedule Waiting Duration / Stay</label>
                            <select id="waiting_minutes" name="waiting_minutes" class="form-select form-control" onchange="resetEstimation()">
                                <option value="0" selected>Direct Transit (No Waiting Charge)</option>
                                <option value="60">1 Hour Stop (+ ₹100.00)</option>
                                <option value="480">8 Hours Stop (+ ₹800.00)</option>
                                <option value="1440">1 Day Stay Over (+ ₹1000.00)</option>
                            </select>
                        </div>

                        <div class="mb-4">
                            <label class="form-label" style="font-weight: 700; font-size: 14px; color: #064e3b; text-transform: uppercase; letter-spacing: 0.5px;">Select Vehicle Type <span class="text-danger">*</span></label>
                            
                            <input type="hidden" id="vehicle_category_passenger" name="vehicle_category" required>
                            <input type="hidden" id="vehicle_category_goods" name="vehicle_category" disabled>

                            <div id="passengerSelectWrapper" class="vehicle-cards-grid">
                                <div class="vehicle-card" data-category="Auto Rickshaw">
                                    <img src="https://img.icons8.com/color/96/auto-rickshaw.png" alt="Auto">
                                    <div class="vehicle-info">
                                        <h5>Auto Rickshaw</h5>
                                        <p>3 seats • Local Budget</p>
                                    </div>
                                    <div class="vehicle-price" id="price-Auto-Rickshaw">--</div>
                                </div>
                                <div class="vehicle-card" data-category="Taxi">
                                    <img src="https://img.icons8.com/color/96/hatchback.png" alt="Taxi">
                                    <div class="vehicle-info">
                                        <h5>Taxi</h5>
                                        <p>4 seats • Comfort</p>
                                    </div>
                                    <div class="vehicle-price" id="price-Taxi">--</div>
                                </div>
                                <div class="vehicle-card" data-category="Standard Cars">
                                    <img src="https://img.icons8.com/color/96/car.png" alt="Standard Cars">
                                    <div class="vehicle-info">
                                        <h5>Standard Sedan</h5>
                                        <p>4 seats • Premium</p>
                                    </div>
                                    <div class="vehicle-price" id="price-Standard-Cars">--</div>
                                </div>
                                <div class="vehicle-card" data-category="8-Seater SUV">
                                    <img src="https://img.icons8.com/color/96/suv.png" alt="SUV">
                                    <div class="vehicle-info">
                                        <h5>8-Seater SUV</h5>
                                        <p>8 seats • Large SUV</p>
                                    </div>
                                    <div class="vehicle-price" id="price-8-Seater-SUV">--</div>
                                </div>
                                <div class="vehicle-card" data-category="MPV">
                                    <img src="https://img.icons8.com/color/96/minivan.png" alt="MPV">
                                    <div class="vehicle-info">
                                        <h5>Family MPV</h5>
                                        <p>6 seats • Comfort</p>
                                    </div>
                                    <div class="vehicle-price" id="price-MPV">--</div>
                                </div>
                                <div class="vehicle-card" data-category="Tempo Traveller">
                                    <img src="https://img.icons8.com/color/96/van.png" alt="Tempo Traveller">
                                    <div class="vehicle-info">
                                        <h5>Tempo Traveller</h5>
                                        <p>12+ seats • Group</p>
                                    </div>
                                    <div class="vehicle-price" id="price-Tempo-Traveller">--</div>
                                </div>
                            </div>

                            <div id="goodsSelectWrapper" class="vehicle-cards-grid strictly-hidden">
                                <div class="vehicle-card" data-category="Goods Auto">
                                    <img src="https://img.icons8.com/color/96/auto-rickshaw.png" alt="Goods Auto" style="filter: hue-rotate(90deg);">
                                    <div class="vehicle-info">
                                        <h5>Goods Auto</h5>
                                        <p>Light local cargo</p>
                                    </div>
                                    <div class="vehicle-price" id="price-Goods-Auto">--</div>
                                </div>
                                <div class="vehicle-card" data-category="Mini Pickup">
                                    <img src="https://img.icons8.com/color/96/pickup.png" alt="Mini Pickup">
                                    <div class="vehicle-info">
                                        <h5>Mini Pickup</h5>
                                        <p>Medium cargo loads</p>
                                    </div>
                                    <div class="vehicle-price" id="price-Mini-Pickup">--</div>
                                </div>
                                <div class="vehicle-card" data-category="Pickup">
                                    <img src="https://img.icons8.com/color/96/delivery-truck.png" alt="Pickup">
                                    <div class="vehicle-info">
                                        <h5>Pickup Truck</h5>
                                        <p>Standard cargo loads</p>
                                    </div>
                                    <div class="vehicle-price" id="price-Pickup">--</div>
                                </div>
                                <div class="vehicle-card" data-category="Lorry">
                                    <img src="https://img.icons8.com/color/96/heavy-truck.png" alt="Lorry">
                                    <div class="vehicle-info">
                                        <h5>Heavy Lorry</h5>
                                        <p>Heavy freight transit</p>
                                    </div>
                                    <div class="vehicle-price" id="price-Lorry">--</div>
                                </div>
                            </div>
                        </div>

                        <div class="mb-3 p-3 rounded" style="background-color: #f8fafc; border: 1px solid #e2e8f0;">
                            <label class="form-label">When do you need the ride? <span class="text-muted" style="font-weight: 400; font-size: 11px;">(Optional)</span></label>
                            <div style="display: flex; gap: 20px; margin-bottom: 10px;">
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="schedule_type" id="ride_now" value="now" checked>
                                    <label class="form-check-label" for="ride_now" style="font-size: 13px;">Right Now</label>
                                </div>
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="schedule_type" id="ride_later" value="later">
                                    <label class="form-check-label" for="ride_later" style="font-size: 13px;">Schedule for Later</label>
                                </div>
                            </div>
                            <input type="datetime-local" id="scheduled_time" name="scheduled_time" class="form-control strictly-hidden">
                        </div>

                        <div id="goodsBlock" class="strictly-hidden border p-3 rounded mb-3" style="background-color: #f9fafb;">
                            <h5 class="font-weight-bold mb-3" style="font-size: 14px;"><i class="fa-solid fa-pallet"></i> Consignment Details</h5>
                            <div class="row gx-3">
                                <div class="col-md-6 mb-2">
                                    <label class="form-label text-secondary">Cargo Description</label>
                                    <input type="text" id="material_description" name="material_description" class="form-control" placeholder="e.g. Furniture" disabled>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label text-secondary">Weight Estimate (Kg)</label>
                                    <input type="number" step="0.1" id="weight" name="weight" class="form-control" placeholder="e.g. 50" disabled>
                                </div>
                            </div>
                        </div>

                        <div class="row mb-4 gx-3">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Payment Option</label>
                                <select id="payment_method" name="payment_method" class="form-select form-control">
                                    <option value="Cash">Cash to Driver</option>
                                    <option value="UPI">UPI / Google Pay</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Promo Code</label>
                                <input type="text" id="promo_code" name="promo_code" class="form-control text-uppercase" placeholder="e.g. KERALA50">
                            </div>
                        </div>

                        <button type="button" id="calcFareBtn" class="btn w-100 py-3 font-weight-bold shadow-sm mb-3" style="border-radius: 8px; background-color: #e5e7eb; color: #111827; border: 1px solid #d1d5db;">
                            <i class="fa-solid fa-calculator me-2"></i> Get Fare Estimate
                        </button>

                        <div id="estimateWidget" class="strictly-hidden card p-4 mb-4" style="background-color: #f0fdf4; border: 1px solid #a7f3d0 !important;">
                            <h5 class="font-weight-bold mb-3 text-dark" style="font-size: 14px; text-transform: uppercase;"><i class="fa-solid fa-circle-check text-success me-1"></i> Pre-Booking Fare Breakdown</h5>
                            <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px;">
                                <span>Estimated Distance:</span>
                                <span id="calcDistance" class="font-weight-bold">-- km (Forward)</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px;">
                                <span>Base Charging:</span>
                                <span id="calcBaseRate" class="font-weight-bold">--</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px;">
                                <span>Rate Per Extra KM:</span>
                                <span id="calcRatePerKm" class="font-weight-bold">--</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px; color: #1e3a8a;">
                                <span>Waiting / Stay Over Charge:</span>
                                <span id="calcWaitingCharge" class="font-weight-bold">+ ₹0.00</span>
                            </div>

                            <div id="returnBreakdown" style="display: flex; justify-content: space-between; font-size: 14px; color: #b45309;">
                                <span class="font-weight-bold">Return Journey Charge:</span>
                                <span id="calcReturnCharge" class="font-weight-bold">+ ₹0.00</span>
                            </div>

                            <div id="promoBreakdown" style="display: flex; justify-content: space-between; font-size: 14px; color: #10b981;" class="strictly-hidden">
                                <span class="font-weight-bold">Coupon Savings:</span>
                                <span id="calcPromo" class="font-weight-bold">- ₹0.00</span>
                            </div>
                            <hr class="my-3">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: 700; font-size: 16px;">Total Payable Amount:</span>
                                <span style="font-weight: 900; color: #064e3b; font-size: 24px;" id="calcFinalTotal">₹0.00</span>
                            </div>
                        </div>

                        <button type="submit" id="bookBtn" class="btn w-100 py-3 font-weight-bold shadow-sm strictly-hidden" style="border-radius: 8px; background-color: #064e3b; color: white; border: none;">
                            <i class="fa-solid fa-car-side me-2"></i> Confirm & Book Ride
                        </button>
                    </form>

                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
let map;
let pickupMarker = null;
let stopoverMarker = null;
let destMarker = null;
let routeLine = null;

function initMap() {
    const kochiCenter = [9.9816, 76.2999];
    map = L.map('map-canvas').setView(kochiCenter, 10);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors © CARTO'
    }).addTo(map);

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const currentCoords = [position.coords.latitude, position.coords.longitude];
                map.flyTo(currentCoords, 13, { duration: 1.5 });
                updateLocationFromCoords(currentCoords[0], currentCoords[1], "pickup");
            },
            (error) => {
                console.log("GPS Location delayed or denied. Using default center.");
            },
            { timeout: 5000, enableHighAccuracy: true }
        );
    }

    map.on('click', function(e) {
        const targetType = document.querySelector('input[name="map_target"]:checked').value;
        updateLocationFromCoords(e.latlng.lat, e.latlng.lng, targetType);
    });

    setTimeout(() => { map.invalidateSize(); }, 400);
}

function extractDistrictFromAddress(addressString) {
    if (!addressString) return;
    const keralaDistricts = ["Ernakulam", "Thiruvananthapuram", "Trivandrum", "Kozhikode", "Thrissur", "Kollam", "Alappuzha", "Kottayam", "Idukki", "Palakkad", "Malappuram", "Wayanad", "Kannur", "Kasaragod", "Pathanamthitta"];
    
    for (let district of keralaDistricts) {
        if (addressString.toLowerCase().includes(district.toLowerCase())) {
            const standardizedName = (district === "Trivandrum") ? "Thiruvananthapuram" : district;
            document.getElementById("pickup_district").value = standardizedName;
            console.log("📡 Engine Context Locked Location District: " + standardizedName);
            return;
        }
    }
}

function updateLocationFromCoords(lat, lng, targetType) {
    const coordinateFallback = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;

    if (targetType === "pickup") {
        if (pickupMarker) { map.removeLayer(pickupMarker); }
        pickupMarker = L.marker([lat, lng]).addTo(map).bindPopup("🛫 Pickup Spot").openPopup();
        document.getElementById("pickup").value = coordinateFallback;
        document.getElementById("pickup_lat").value = lat;
        document.getElementById("pickup_lng").value = lng;
        
        if (document.getElementById("stopoverContainerCol").classList.contains("strictly-hidden")) {
            document.getElementById("target_dest").checked = true;
        } else {
            document.getElementById("target_stopover").checked = true;
        }

        fetch(`https://photon.komoot.io/reverse?lon=${lng}&lat=${lat}`)
            .then(res => res.json())
            .then(data => {
                if (data.features && data.features.length > 0) {
                    const props = data.features[0].properties;
                    const name = props.name || "";
                    const district = props.district || props.city || "";
                    const fullAddress = district ? `${name}, ${district}` : name;
                    if (fullAddress.trim().length > 2) {
                        document.getElementById("pickup").value = fullAddress;
                        extractDistrictFromAddress(fullAddress);
                    }
                }
            }).catch(e => console.log("Lookup failure. Retaining raw coordinates."));

    } else if (targetType === "stopover") {
        if (stopoverMarker) { map.removeLayer(stopoverMarker); }
        stopoverMarker = L.marker([lat, lng]).addTo(map).bindPopup("🛑 Stopover Point").openPopup();
        document.getElementById("stopover").value = coordinateFallback;
        document.getElementById("stopover_lat").value = lat;
        document.getElementById("stopover_lng").value = lng;
        document.getElementById("target_dest").checked = true;

        fetch(`https://photon.komoot.io/reverse?lon=${lng}&lat=${lat}`)
            .then(res => res.json())
            .then(data => {
                if (data.features && data.features.length > 0) {
                    const props = data.features[0].properties;
                    const name = props.name || "";
                    const district = props.district || props.city || "";
                    const fullAddress = district ? `${name}, ${district}` : name;
                    if (fullAddress.trim().length > 2) {
                        document.getElementById("stopover").value = fullAddress;
                    }
                }
            }).catch(e => console.log("Lookup failure. Retaining raw coordinates."));

    } else {
        if (destMarker) { map.removeLayer(destMarker); }
        destMarker = L.marker([lat, lng]).addTo(map).bindPopup("🛬 Destination Spot").openPopup();
        document.getElementById("destination").value = coordinateFallback;
        document.getElementById("dest_lat").value = lat;
        document.getElementById("dest_lng").value = lng;
        
        fetch(`https://photon.komoot.io/reverse?lon=${lng}&lat=${lat}`)
            .then(res => res.json())
            .then(data => {
                if (data.features && data.features.length > 0) {
                    const props = data.features[0].properties;
                    const name = props.name || "";
                    const district = props.district || props.city || "";
                    const fullAddress = district ? `${name}, ${district}` : name;
                    if (fullAddress.trim().length > 2) {
                        document.getElementById("destination").value = fullAddress;
                    }
                }
            }).catch(e => console.log("Lookup failure. Retaining raw coordinates."));
    }
    resetEstimation();
}

function setupAutocomplete(inputElement, suggestionsElement, targetType) {
    let debounceTimer;

    inputElement.addEventListener("input", function() {
        clearTimeout(debounceTimer);
        const query = inputElement.value.trim();
        if (query.length < 3) {
            suggestionsElement.classList.add("strictly-hidden");
            return;
        }

        debounceTimer = setTimeout(() => {
            const searchUrl = `https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&lat=10.0&lon=76.5&limit=5`;
            fetch(searchUrl)
                .then(res => res.json())
                .then(data => {
                    suggestionsElement.innerHTML = "";
                    if (data.features && data.features.length > 0) {
                        suggestionsElement.classList.remove("strictly-hidden");
                        data.features.forEach(feature => {
                            const props = feature.properties;
                            const lonLat = feature.geometry.coordinates;
                            const name = props.name || "";
                            const city = props.city || props.district || props.state || "";
                            const fullLabel = city ? `${name}, ${city}` : name;

                            const li = document.createElement("li");
                            li.innerText = fullLabel;
                            li.addEventListener("click", function() {
                                inputElement.value = fullLabel;
                                suggestionsElement.classList.add("strictly-hidden");
                                
                                if (targetType === "pickup") {
                                    extractDistrictFromAddress(fullLabel);
                                    if (pickupMarker) { map.removeLayer(pickupMarker); }
                                    pickupMarker = L.marker([lonLat[1], lonLat[0]]).addTo(map).bindPopup("🛫 Pickup Spot").openPopup();
                                    document.getElementById("pickup_lat").value = lonLat[1];
                                    document.getElementById("pickup_lng").value = lonLat[0];
                                    if (document.getElementById("stopoverContainerCol").classList.contains("strictly-hidden")) {
                                        document.getElementById("target_dest").checked = true;
                                    } else {
                                        document.getElementById("target_stopover").checked = true;
                                    }
                                } else if (targetType === "stopover") {
                                    if (stopoverMarker) { map.removeLayer(stopoverMarker); }
                                    stopoverMarker = L.marker([lonLat[1], lonLat[0]]).addTo(map).bindPopup("🛑 Stopover Point").openPopup();
                                    document.getElementById("stopover_lat").value = lonLat[1];
                                    document.getElementById("stopover_lng").value = lonLat[0];
                                    document.getElementById("target_dest").checked = true;
                                } else {
                                    if (destMarker) { map.removeLayer(destMarker); }
                                    destMarker = L.marker([lonLat[1], lonLat[0]]).addTo(map).bindPopup("🛬 Destination Spot").openPopup();
                                    document.getElementById("dest_lat").value = lonLat[1];
                                    document.getElementById("dest_lng").value = lonLat[0];
                                }
                                resetEstimation();
                                map.flyTo([lonLat[1], lonLat[0]], 14, { duration: 1 });
                            });
                            suggestionsElement.appendChild(li);
                        });
                    } else {
                        suggestionsElement.classList.add("strictly-hidden");
                    }
                })
                .catch(err => console.log("Search request delayed."));
        }, 300);
    });

    document.addEventListener("click", function(e) {
        if (e.target !== inputElement) {
            suggestionsElement.classList.add("strictly-hidden");
        }
    });
}

function addStopoverField() {
    document.getElementById('stopoverContainerCol').classList.remove('strictly-hidden');
    document.getElementById('addStopHudSection').classList.add('strictly-hidden');
    
    document.getElementById('pickupContainerCol').className = "col-md-4 mb-3 autocomplete-container";
    document.getElementById('destContainerCol').className = "col-md-4 mb-3 autocomplete-container";
    resetEstimation();
}

function removeStopoverField() {
    document.getElementById('stopoverContainerCol').classList.add('strictly-hidden');
    document.getElementById('addStopHudSection').classList.remove('strictly-hidden');
    document.getElementById('stopover').value = '';
    document.getElementById('stopover_lat').value = '';
    document.getElementById('stopover_lng').value = '';
    
    if (stopoverMarker) {
        map.removeLayer(stopoverMarker);
        stopoverMarker = null;
    }
    
    document.getElementById('pickupContainerCol').className = "col-md-6 mb-3 autocomplete-container";
    document.getElementById('destContainerCol').className = "col-md-6 mb-3 autocomplete-container";
    document.getElementById('target_dest').checked = true;
    resetEstimation();
}

document.addEventListener("DOMContentLoaded", function() {
    initMap();

    const pickupInput = document.getElementById("pickup");
    const stopoverInput = document.getElementById("stopover");
    const destInput = document.getElementById("destination");
    const pickupSuggestions = document.getElementById("pickup-suggestions");
    const stopoverSuggestions = document.getElementById("stopover-suggestions");
    const destSuggestions = document.getElementById("dest-suggestions");

    setupAutocomplete(pickupInput, pickupSuggestions, "pickup");
    setupAutocomplete(stopoverInput, stopoverSuggestions, "stopover");
    setupAutocomplete(destInput, destSuggestions, "destination");

    document.getElementById('ride_later').addEventListener('change', function() {
        const timeInput = document.getElementById('scheduled_time');
        timeInput.classList.remove('strictly-hidden');
        timeInput.required = true;
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        timeInput.min = now.toISOString().slice(0, 16);
    });
    
    document.getElementById('ride_now').addEventListener('change', function() {
        const timeInput = document.getElementById('scheduled_time');
        timeInput.classList.add('strictly-hidden');
        timeInput.required = false;
        timeInput.value = '';
    });

    const tabPassenger = document.getElementById("tabPassenger");
    const tabGoods = document.getElementById("tabGoods");
    const bookingTypeInput = document.getElementById("booking_type");
    const passengerSelectWrapper = document.getElementById("passengerSelectWrapper");
    const passengerSelect = document.getElementById("vehicle_category_passenger");
    const goodsSelectWrapper = document.getElementById("goodsSelectWrapper");
    const goodsSelect = document.getElementById("vehicle_category_goods");
    const goodsBlock = document.getElementById("goodsBlock");
    const materialDescription = document.getElementById("material_description");
    const weightInput = document.getElementById("weight");
    const promoInput = document.getElementById("promo_code");
    const calcFareBtn = document.getElementById("calcFareBtn");
    const bookBtn = document.getElementById("bookBtn");
    const estimateWidget = document.getElementById("estimateWidget");
    const calcDistance = document.getElementById("calcDistance");
    const calcBaseRate = document.getElementById("calcBaseRate");
    const calcRatePerKm = document.getElementById("calcRatePerKm");
    const promoBreakdown = document.getElementById("promoBreakdown");
    const calcPromo = document.getElementById("calcPromo");
    const calcFinalTotal = document.getElementById("calcFinalTotal");

    let calculatedEstimates = null;

    const passengerCards = document.querySelectorAll("#passengerSelectWrapper .vehicle-card");
    const goodsCards = document.querySelectorAll("#goodsSelectWrapper .vehicle-card");

    function selectVehicleCard(card, isGoods) {
        const wrapper = isGoods ? goodsSelectWrapper : passengerSelectWrapper;
        const targetInput = isGoods ? goodsSelect : passengerSelect;
        
        wrapper.querySelectorAll(".vehicle-card").forEach(c => c.classList.remove("selected"));
        card.classList.add("selected");
        
        const catValue = card.getAttribute("data-category");
        targetInput.value = catValue;
        
        if (calculatedEstimates && calculatedEstimates[catValue]) {
            updateFareBreakdownWidget(catValue, calculatedEstimates[catValue]);
        } else {
            resetEstimation();
        }
    }

    passengerCards.forEach(card => {
        card.addEventListener("click", () => selectVehicleCard(card, false));
    });

    goodsCards.forEach(card => {
        card.addEventListener("click", () => selectVehicleCard(card, true));
    });

    const urlParams = new URLSearchParams(window.location.search);
    const initialType = urlParams.get('booking_type');
    if (initialType === 'goods') {
        renderTab("goods");
    } else {
        renderTab("passenger");
    }

    function resetEstimation() {
        estimateWidget.classList.add("strictly-hidden");
        bookBtn.classList.add("strictly-hidden");
        calcFareBtn.innerHTML = '<i class="fa-solid fa-calculator me-2"></i> Get Fare Estimate';
        calcFareBtn.classList.remove("strictly-hidden");
        calculatedEstimates = null;
        document.querySelectorAll(".vehicle-price").forEach(el => el.innerText = "--");
        
        if (routeLine) {
            map.removeLayer(routeLine);
            routeLine = null;
        }
    }

    function updateFareBreakdownWidget(category, details) {
        estimateWidget.classList.remove("strictly-hidden");
        
        if (details.is_outstation) {
            calcBaseRate.innerText = `N/A (Outstation Flat Rate)`;
        } else {
            calcBaseRate.innerText = `₹${details.base_fare} (incl. first ${details.base_distance} km)`;
        }

        calcRatePerKm.innerText = `₹${details.rate_per_km}/km`;
        document.getElementById("calcReturnCharge").innerText = `+ ₹${details.return_charge.toFixed(2)}`;
        document.getElementById("calcWaitingCharge").innerText = `+ ₹${details.waiting_charge.toFixed(2)}`;

        if (details.discount > 0) {
            promoBreakdown.classList.remove("strictly-hidden");
            calcPromo.innerText = `- ₹${details.discount.toFixed(2)}`;
        } else {
            promoBreakdown.classList.add("strictly-hidden");
        }

        calcFinalTotal.innerText = `₹${details.final_fare.toFixed(2)}`;
        document.getElementById("estimated_fare").value = details.final_fare.toFixed(2);
        
        bookBtn.classList.remove("strictly-hidden");
        calcFareBtn.classList.add("strictly-hidden");
    }

    function renderTab(targetMode) {
        resetEstimation();
        document.querySelectorAll(".vehicle-card").forEach(c => c.classList.remove("selected"));
        passengerSelect.value = "";
        goodsSelect.value = "";
        
        if (typeof map !== 'undefined' && map) {
            setTimeout(() => { map.invalidateSize(); }, 150);
        }

        if (targetMode === "goods") {
            bookingTypeInput.value = "goods";
            tabGoods.classList.add("active");
            tabPassenger.classList.remove("active");
            passengerSelectWrapper.classList.add("strictly-hidden");
            passengerSelect.disabled = true;
            passengerSelect.removeAttribute('required');
            goodsSelectWrapper.classList.remove("strictly-hidden");
            goodsSelect.disabled = false;
            goodsSelect.setAttribute('required', 'required');
            goodsBlock.classList.remove("strictly-hidden");
            materialDescription.disabled = false;
            weightInput.disabled = false;
            document.getElementById('waitingChargeWrapper').classList.add('strictly-hidden');
        } else {
            bookingTypeInput.value = "passenger";
            tabPassenger.classList.add("active");
            tabGoods.classList.remove("active");
            goodsSelectWrapper.classList.add("strictly-hidden");
            goodsSelect.disabled = true;
            goodsSelect.removeAttribute('required');
            passengerSelectWrapper.classList.remove("strictly-hidden");
            passengerSelect.disabled = false;
            passengerSelect.setAttribute('required', 'required');
            goodsBlock.classList.add("strictly-hidden");
            materialDescription.disabled = true;
            weightInput.disabled = true;
            document.getElementById('waitingChargeWrapper').classList.remove('strictly-hidden');
        }
    }

    tabPassenger.addEventListener("click", () => renderTab("passenger"));
    tabGoods.addEventListener("click", () => renderTab("goods"));

    pickupInput.addEventListener("input", resetEstimation);
    stopoverInput.addEventListener("input", resetEstimation);
    destInput.addEventListener("input", resetEstimation);

    calcFareBtn.addEventListener("click", function() {
        const pickup = pickupInput.value.trim();
        const destination = destInput.value.trim();
        const category = bookingTypeInput.value === "goods" ? goodsSelect.value : passengerSelect.value;
        const promo_code = promoInput.value.trim();
        const waiting_minutes = document.getElementById("waiting_minutes").value;

        if (!pickup || !destination) {
            alert("Please choose precise locations from the interactive map canvas.");
            return;
        }
        if (!category) {
            alert("Please select a vehicle type from the options above.");
            return;
        }

        calcFareBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Calculating Fare...';

        fetch("/customer/estimate-fare", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token() }}"
            },
            body: JSON.stringify({ 
                pickup: pickup,
                stopover: stopoverInput.value.trim(),
                destination: destination, 
                category: category, 
                promo_code: promo_code,
                waiting_minutes: waiting_minutes,
                pickup_lat: document.getElementById("pickup_lat").value,
                pickup_lng: document.getElementById("pickup_lng").value,
                stopover_lat: document.getElementById("stopover_lat").value,
                stopover_lng: document.getElementById("stopover_lng").value,
                dest_lat: document.getElementById("dest_lat").value,
                dest_lng: document.getElementById("dest_lng").value
            })
        })
        .then(res => res.json())
        .then(data => {
            calcFareBtn.innerHTML = '<i class="fa-solid fa-rotate-right me-2"></i> Recalculate Fare';
            if (data.success) {
                calculatedEstimates = data.estimates;

                if (data.estimates) {
                    Object.keys(data.estimates).forEach(cat => {
                        const priceEl = document.getElementById(`price-${cat.replace(/\s+/g, '-')}`);
                        if (priceEl) {
                            priceEl.innerText = `₹${data.estimates[cat].final_fare.toFixed(0)}`;
                        }
                    });
                }

                calcDistance.innerText = `${data.distance_km} km (Combined Journey)`;

                const currentDetails = data.estimates[category];
                if (currentDetails) {
                    updateFareBreakdownWidget(category, currentDetails);
                }

                if (routeLine) { map.removeLayer(routeLine); }

                if (data.route_geometry) {
                    routeLine = L.geoJSON(data.route_geometry, {
                        style: {
                            color: '#064e3b',
                            weight: 5,
                            opacity: 0.85
                        }
                    }).addTo(map);

                    map.fitBounds(routeLine.getBounds(), { padding: [40, 40] });
                }

            } else {
                alert(data.error || "Failed to calculate fare.");
            }
        })
        .catch(err => {
            calcFareBtn.innerHTML = '<i class="fa-solid fa-calculator me-2"></i> Get Fare Estimate';
            alert("Network routing calculation connection failed.");
        });
    });

    const bookingForm = document.getElementById("bookingForm");
    bookingForm.addEventListener("submit", function(e) {
        const pickup = pickupInput.value.trim();
        const destination = destInput.value.trim();
        const category = bookingTypeInput.value === "goods" ? goodsSelect.value : passengerSelect.value;
        const p_lat = document.getElementById("pickup_lat").value;
        const d_lat = document.getElementById("dest_lat").value;
        
        if (!pickup || !destination || !category || !p_lat || !d_lat) {
            e.preventDefault();
            alert("Please make sure you drop both pins on the map and choose a vehicle type before booking!");
            return false;
        }

        bookBtn.disabled = true;
        bookBtn.style.opacity = "0.7";
        bookBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Securing Ride...';
    });
});
</script>
{% endblock %}
