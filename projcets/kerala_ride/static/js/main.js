// KeralaRide Connect UI Interactions
document.addEventListener("DOMContentLoaded", function() {
    // Dismiss alerts smoothly
    const closeButtons = document.querySelectorAll(".alert-close");
    closeButtons.forEach(button => {
        button.addEventListener("click", function() {
            const alert = this.closest(".alert");
            if (alert) {
                alert.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                setTimeout(() => alert.remove(), 200);
            }
        });
    });

    // Auto-fade flash messages after 5 seconds
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});
