function speakText(text) {
    const speech = new SpeechSynthesisUtterance(text);
    speech.rate = 1;
    speech.pitch = 1;
    speech.volume = 1;
    window.speechSynthesis.speak(speech);
}
function getLocation() {
    if (!navigator.geolocation) {
        alert("Geolocation not supported");
        return;
    }

    navigator.geolocation.getCurrentPosition(function(position) {
        document.getElementById("lat").value = position.coords.latitude;
        document.getElementById("lon").value = position.coords.longitude;

        alert("Location captured! Now click Analyze.");
    });
}
let total = 0;

function addToCart(product, price) {
    let item = document.createElement("li");
    item.textContent = product + " - ₹" + price;
    document.getElementById("cartItems").appendChild(item);

    total += price;
    document.getElementById("total").textContent = total;
}

function checkout() {
    if (total === 0) {
        alert("Cart is empty");
        return;
    }

    let method = prompt("Select Payment Method:\n1. UPI\n2. Card\n3. Cash");

    if (method === null) {
        return;
    }

    alert("Payment Successful!\nTotal Amount: ₹" + total);

    document.getElementById("cartItems").innerHTML = "";
    total = 0;
    document.getElementById("total").textContent = total;
}

document.addEventListener("DOMContentLoaded", function () {
    const reveals = document.querySelectorAll(".reveal");

    function revealOnScroll() {
        const windowHeight = window.innerHeight;

        reveals.forEach((element) => {
            const top = element.getBoundingClientRect().top;
            if (top < windowHeight - 80) {
                element.classList.add("active");
            }
        });
    }

    revealOnScroll();
    window.addEventListener("scroll", revealOnScroll);
});

document.addEventListener("DOMContentLoaded", function () {
    // ===== Scroll reveal =====
    const reveals = document.querySelectorAll(".reveal");

    function revealOnScroll() {
        const windowHeight = window.innerHeight;

        reveals.forEach((element) => {
            const top = element.getBoundingClientRect().top;
            if (top < windowHeight - 80) {
                element.classList.add("active");
            }
        });
    }

    revealOnScroll();
    window.addEventListener("scroll", revealOnScroll);

    // ===== Animated counters =====
    const counters = document.querySelectorAll(".counter");

    counters.forEach(counter => {
        const target = parseFloat(counter.getAttribute("data-target")) || 0;
        let current = 0;
        const increment = target / 60;

        function updateCounter() {
            if (current < target) {
                current += increment;
                if (target % 1 !== 0) {
                    counter.innerText = current.toFixed(1);
                } else {
                    counter.innerText = Math.ceil(current);
                }
                requestAnimationFrame(updateCounter);
            } else {
                counter.innerText = target % 1 !== 0 ? target.toFixed(1) : target;
            }
        }

        updateCounter();
    });

    // ===== Floating particles =====
    const particlesContainer = document.getElementById("particles");
    if (particlesContainer) {
        for (let i = 0; i < 22; i++) {
            const particle = document.createElement("div");
            particle.classList.add("particle");
            particle.style.left = Math.random() * 100 + "%";
            particle.style.animationDuration = (6 + Math.random() * 8) + "s";
            particle.style.animationDelay = (Math.random() * 5) + "s";
            particle.style.opacity = Math.random().toFixed(2);
            particle.style.width = particle.style.height = (4 + Math.random() * 10) + "px";
            particlesContainer.appendChild(particle);
        }
    }
});

function toggleMenu() {
    const menu = document.getElementById("mobileMenu");
    menu.classList.toggle("show-menu");
}

function startVoice() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = navigator.language || 'en-US';
    recognition.start();

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById("chatInput").value = transcript;
    };

    recognition.onerror = function () {
        alert("Voice recognition failed. Try again.");
    };
}

function speakText(text) {
    const speech = new SpeechSynthesisUtterance(text);

    // 🌍 match language
    speech.lang = navigator.language || 'en-US';

    speech.rate = 1;
    speech.pitch = 1;

    speechSynthesis.speak(speech);
}

async function refreshSensorDashboard() {
    try {
        const response = await fetch("/api/sensor-data");
        const data = await response.json();

        const soil = document.getElementById("soil_moisture_value");
        const temp = document.getElementById("field_temperature_value");
        const humidity = document.getElementById("field_humidity_value");
        const rain = document.getElementById("rain_detected_value");
        const ph = document.getElementById("soil_ph_value");
        const updated = document.getElementById("last_updated_value");

        if (soil) soil.innerText = data.soil_moisture;
        if (temp) temp.innerText = data.field_temperature;
        if (humidity) humidity.innerText = data.field_humidity;
        if (rain) rain.innerText = data.rain_detected;
        if (ph) ph.innerText = data.soil_ph;
        if (updated) updated.innerText = data.last_updated;

        // Optional chart update
        if (window.sensorChartInstance) {
            window.sensorChartInstance.data.datasets[0].data = [
                Number(data.soil_moisture),
                Number(data.field_temperature),
                Number(data.field_humidity),
                Number(data.soil_ph)
            ];
            window.sensorChartInstance.update();
        }

    } catch (error) {
        console.log("Sensor refresh failed:", error);
    }
}

// Auto-refresh every 5 seconds
setInterval(refreshSensorDashboard, 5000);

let simulationInterval = null;

function startSimulation(event) {
    event.preventDefault();

    if (simulationInterval) return;

    simulationInterval = setInterval(async () => {
        try {
            await fetch("/api/simulate-sensor", {
                method: "POST"
            });
            refreshSensorDashboard();
        } catch (error) {
            console.log("Simulation error:", error);
        }
    }, 5000);
}

function stopSimulation() {
    clearInterval(simulationInterval);
    simulationInterval = null;
}