// KeralaRide Connect Interactive Map Visualizer
// Draw a custom canvas-based stylized map of Kerala districts and handle live vehicle tracking animations

const KERALA_HUBS = {
    "Trivandrum": { name: "Thiruvananthapuram", x: 190, y: 400 },
    "Kollam": { name: "Kollam", x: 170, y: 360 },
    "Pathanamthitta": { name: "Pathanamthitta", x: 200, y: 330 },
    "Alappuzha": { name: "Alappuzha", x: 145, y: 315 },
    "Kottayam": { name: "Kottayam", x: 175, y: 290 },
    "Idukki": { name: "Idukki", x: 220, y: 260 },
    "Ernakulam": { name: "Kochi (Ernakulam)", x: 150, y: 240 },
    "Thrissur": { name: "Thrissur", x: 165, y: 190 },
    "Palakkad": { name: "Palakkad", x: 210, y: 160 },
    "Malappuram": { name: "Malappuram", x: 155, y: 130 },
    "Kozhikode": { name: "Kozhikode", x: 135, y: 100 },
    "Wayanad": { name: "Wayanad", x: 165, y: 80 },
    "Kannur": { name: "Kannur", x: 105, y: 60 },
    "Kasaragod": { name: "Kasaragod", x: 80, y: 30 }
};

class KeralaMapTracker {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.options = Object.assign({
            status: 'Pending',
            pickup: 'Ernakulam',
            destination: 'Thrissur',
            vehicleCategory: 'Auto Rickshaw'
        }, options);
        
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        
        // Match hubs from pickup and destination descriptions
        this.pickupHub = this.matchHub(this.options.pickup) || KERALA_HUBS["Ernakulam"];
        this.destHub = this.matchHub(this.options.destination) || KERALA_HUBS["Thrissur"];
        
        // Vehicle animation state
        this.progress = 0.0; // 0.0 to 1.0
        this.animationSpeed = 0.002;
        this.driverPos = { x: this.pickupHub.x - 30, y: this.pickupHub.y + 20 }; // Driver starting point
        
        // Start animation loop
        this.active = true;
        this.animate();
    }
    
    matchHub(addressString) {
        if (!addressString) return null;
        const lower = addressString.toLowerCase();
        for (const key in KERALA_HUBS) {
            if (lower.includes(key.toLowerCase()) || lower.includes(KERALA_HUBS[key].name.toLowerCase())) {
                return KERALA_HUBS[key];
            }
        }
        return null;
    }
    
    resizeCanvas() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }
    
    updateStatus(newStatus) {
        this.options.status = newStatus;
    }
    
    animate() {
        if (!this.active) return;
        this.draw();
        this.updateState();
        requestAnimationFrame(() => this.animate());
    }
    
    updateState() {
        const status = this.options.status;
        
        if (status === 'Accepted') {
            // Driver is moving from their mock initial position towards the pickup hub
            const dx = this.pickupHub.x - this.driverPos.x;
            const dy = this.pickupHub.y - this.driverPos.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist > 2) {
                this.driverPos.x += (dx / dist) * 0.8;
                this.driverPos.y += (dy / dist) * 0.8;
            } else {
                this.driverPos.x = this.pickupHub.x;
                this.driverPos.y = this.pickupHub.y;
            }
        } else if (status === 'Arrived') {
            // Driver is at pickup location
            this.driverPos.x = this.pickupHub.x;
            this.driverPos.y = this.pickupHub.y;
        } else if (status === 'Active') {
            // Trip is active: vehicle is moving from pickup to destination
            this.progress += this.animationSpeed;
            if (this.progress > 1.0) {
                this.progress = 1.0;
            }
            
            // Linear interpolation between pickup and destination
            this.driverPos.x = this.pickupHub.x + (this.destHub.x - this.pickupHub.x) * this.progress;
            this.driverPos.y = this.pickupHub.y + (this.destHub.y - this.pickupHub.y) * this.progress;
            
            // Update ETA text on parent DOM if present
            const etaElement = document.getElementById("eta-value");
            if (etaElement) {
                const remainingPercent = 1.0 - this.progress;
                const etaMin = Math.ceil(remainingPercent * 25);
                etaElement.innerText = etaMin > 0 ? `${etaMin} mins` : "Arrived";
            }
        } else if (status === 'Completed') {
            this.driverPos.x = this.destHub.x;
            this.driverPos.y = this.destHub.y;
            this.progress = 1.0;
        }
    }
    
    draw() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        
        ctx.clearRect(0, 0, w, h);
        
        // 1. Draw Map Background (Ocean Grid)
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        const gridSize = 40;
        for (let x = 0; x < w; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, h);
            ctx.stroke();
        }
        for (let y = 0; y < h; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(w, y);
            ctx.stroke();
        }
        
        // 2. Draw Stylized Coastline of Kerala (simple curve from Top-Left to Bottom-Right)
        ctx.fillStyle = '#f0fdf4'; // Light green land
        ctx.beginPath();
        ctx.moveTo(0, h);
        
        // Simple curve approximation for Kerala shape
        ctx.lineTo(0, 0);
        ctx.bezierCurveTo(w * 0.1, h * 0.1, w * 0.4, h * 0.5, w * 0.65, h);
        ctx.closePath();
        ctx.fill();
        
        // Coastal stroke
        ctx.strokeStyle = '#86efac';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.bezierCurveTo(w * 0.1, h * 0.1, w * 0.4, h * 0.5, w * 0.65, h);
        ctx.stroke();
        
        // 3. Draw District Network Connections
        ctx.strokeStyle = 'rgba(6, 78, 59, 0.1)';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        
        // Connect Kasaragod down to TVM along the coast
        const hubKeys = Object.keys(KERALA_HUBS);
        for (let i = 0; i < hubKeys.length - 1; i++) {
            const start = KERALA_HUBS[hubKeys[i]];
            const end = KERALA_HUBS[hubKeys[i + 1]];
            
            // Map coordinates relative to standard dimensions (250x450 scale to fit canvas width/height)
            const x1 = (start.x / 300) * w;
            const y1 = (start.y / 450) * h;
            const x2 = (end.x / 300) * w;
            const y2 = (end.y / 450) * h;
            
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
        }
        ctx.stroke();
        ctx.setLineDash([]); // Reset line dash
        
        // 4. Draw Hub Nodes
        for (const key in KERALA_HUBS) {
            const hub = KERALA_HUBS[key];
            const hx = (hub.x / 300) * w;
            const hy = (hub.y / 450) * h;
            
            const isPickup = hub.name === this.pickupHub.name;
            const isDest = hub.name === this.destHub.name;
            
            if (isPickup) {
                ctx.fillStyle = '#2563eb'; // Blue for pickup
                ctx.beginPath();
                ctx.arc(hx, hy, 8, 0, 2 * Math.PI);
                ctx.fill();
                
                ctx.strokeStyle = 'rgba(37, 99, 235, 0.3)';
                ctx.lineWidth = 6;
                ctx.beginPath();
                ctx.arc(hx, hy, 14, 0, 2 * Math.PI);
                ctx.stroke();
            } else if (isDest) {
                ctx.fillStyle = '#d97706'; // Gold/Amber for destination
                ctx.beginPath();
                ctx.arc(hx, hy, 8, 0, 2 * Math.PI);
                ctx.fill();
                
                ctx.strokeStyle = 'rgba(217, 119, 6, 0.3)';
                ctx.lineWidth = 6;
                ctx.beginPath();
                ctx.arc(hx, hy, 14, 0, 2 * Math.PI);
                ctx.stroke();
            } else {
                ctx.fillStyle = '#064e3b'; // Standard node green
                ctx.beginPath();
                ctx.arc(hx, hy, 4, 0, 2 * Math.PI);
                ctx.fill();
            }
            
            // Label important hubs or print in smaller text
            if (isPickup || isDest || h > 300) {
                ctx.fillStyle = '#1f2937';
                ctx.font = 'bold 11px Outfit';
                ctx.fillText(hub.name.split(" ")[0], hx + 10, hy + 4);
            }
        }
        
        // 5. Draw Active Trip Route
        if (this.options.status !== 'Pending') {
            const px = (this.pickupHub.x / 300) * w;
            const py = (this.pickupHub.y / 450) * h;
            const dx = (this.destHub.x / 300) * w;
            const dy = (this.destHub.y / 300) * w; // Wait, scale properly relative to h
            const dy_scale = (this.destHub.y / 450) * h;
            
            ctx.strokeStyle = '#0284c7';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(dx, dy_scale);
            ctx.stroke();
        }
        
        // 6. Draw Vehicle Marker
        if (this.options.status !== 'Pending') {
            const vx = (this.driverPos.x / 300) * w;
            const vy = (this.driverPos.y / 450) * h;
            
            // Outer glow ring
            ctx.strokeStyle = 'rgba(22, 163, 74, 0.4)';
            ctx.lineWidth = 8;
            ctx.beginPath();
            ctx.arc(vx, vy, 10, 0, 2 * Math.PI);
            ctx.stroke();
            
            // Inner circle
            ctx.fillStyle = '#16a34a'; // Vehicle green
            ctx.beginPath();
            ctx.arc(vx, vy, 6, 0, 2 * Math.PI);
            ctx.fill();
            
            // Vehicle Category Tag
            ctx.fillStyle = '#1e293b';
            ctx.font = 'bold 10px Outfit';
            const catText = `${this.options.vehicleCategory} (Driver)`;
            const textWidth = ctx.measureText(catText).width;
            
            ctx.fillRect(vx - (textWidth/2) - 4, vy - 24, textWidth + 8, 14);
            ctx.fillStyle = '#ffffff';
            ctx.fillText(catText, vx - (textWidth/2), vy - 14);
        }
    }
}

window.KeralaMapTracker = KeralaMapTracker;
