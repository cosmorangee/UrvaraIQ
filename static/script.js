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