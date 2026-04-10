from flask import Flask, render_template, request
import requests

app = Flask(__name__)

latest_sensor_data = {
    "soil_moisture": 45,
    "field_temperature": 30,
    "field_humidity": 70,
    "rain_detected": "No",
    "soil_ph": 6.8
}

API_KEY = "36370ec06147479a4eaba85f29ceef1d"

def get_sensor_recommendation(sensor_data):
    advice = []

    soil_moisture = float(sensor_data.get("soil_moisture", 0))
    field_temperature = float(sensor_data.get("field_temperature", 0))
    field_humidity = float(sensor_data.get("field_humidity", 0))
    rain_detected = sensor_data.get("rain_detected", "No")
    soil_ph = float(sensor_data.get("soil_ph", 7))

    if soil_moisture < 30:
        advice.append("Soil moisture is low. Irrigation is needed soon.")
    elif soil_moisture > 75:
        advice.append("Soil is already very wet. Avoid irrigation to prevent waterlogging.")
    else:
        advice.append("Soil moisture is in a moderate range.")

    if field_temperature > 35:
        advice.append("Field temperature is high. Irrigate during early morning or evening.")
    elif field_temperature < 15:
        advice.append("Temperature is low. Crop growth may slow down.")

    if field_humidity > 80:
        advice.append("High field humidity detected. There is increased fungal disease risk.")

    if rain_detected == "Yes":
        advice.append("Rain is detected. Delay irrigation and check field drainage.")

    if soil_ph < 5.5:
        advice.append("Soil appears acidic. Consider pH correction before fertilizer planning.")
    elif soil_ph > 8:
        advice.append("Soil appears alkaline. Nutrient absorption may be affected.")
    else:
        advice.append("Soil pH is in a generally acceptable range.")

    return advice

def get_coordinates(place):
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": place,
        "limit": 1,
        "appid": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    print("Geocoding response:", data)

    if response.status_code == 200 and len(data) > 0:
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        display_name = data[0]["name"]
        state = data[0].get("state", "")
        country = data[0].get("country", "")
        return lat, lon, display_name, state, country, None

    return None, None, None, None, None, "Location not found. Try village name with district/state."


def get_weather_by_coordinates(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params)
    data = response.json()

    print("Weather response:", data)

    if response.status_code == 200 and "main" in data:
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        weather_desc = data["weather"][0]["description"].title()
        wind_speed = data["wind"]["speed"]
        return temp, humidity, weather_desc, wind_speed, None

    return None, None, None, None, data.get("message", "Could not fetch weather data.")


def get_recommendation(temp, humidity):
    if temp > 35:
        irrigation = "High water needed 💧"
    elif temp > 25:
        irrigation = "Moderate irrigation needed 🌿"
    else:
        irrigation = "Low irrigation needed ✅"

    if humidity > 80:
        disease = "High risk of fungal disease ⚠️"
        fertilizer = "Use disease-safe organic support and monitor leaves."
        alert = "Humidity is very high. Crop disease chances are increased."
    else:
        disease = "Low disease risk 🌱"
        fertilizer = "Balanced fertilizer recommended."
        alert = "Conditions look stable for now."

    return irrigation, disease, fertilizer, alert

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/analyzer", methods=["GET", "POST"])
def analyzer():
    result = None
    error = None

    if request.method == "POST":
        place = request.form.get("place", "").strip()
        crop = request.form.get("crop")
        lat = request.form.get("lat", "").strip()
        lon = request.form.get("lon", "").strip()

        # If GPS coordinates are available, use them first
        if lat and lon:
            temp, humidity, weather_desc, wind_speed, weather_error = get_weather_by_coordinates(lat, lon)

            if weather_error:
                error = weather_error
            else:
                irrigation, disease, fertilizer, alert = get_recommendation(temp, humidity)

                result = {
                    "place": "Current Location",
                    "state": "",
                    "country": "",
                    "crop": crop,
                    "lat": lat,
                    "lon": lon,
                    "temp": temp,
                    "humidity": humidity,
                    "weather_desc": weather_desc,
                    "wind_speed": wind_speed,
                    "irrigation": irrigation,
                    "disease": disease,
                    "fertilizer": fertilizer,
                    "alert": alert
                }

        # Otherwise use typed place name
        elif place:
            lat, lon, display_name, state, country, geo_error = get_coordinates(place)

            if geo_error:
                error = geo_error
            else:
                temp, humidity, weather_desc, wind_speed, weather_error = get_weather_by_coordinates(lat, lon)

                if weather_error:
                    error = weather_error
                else:
                    # Weather-based recommendation
                    irrigation, disease, fertilizer, alert = get_recommendation(temp, humidity)

                    # NEW: Sensor-based recommendation
                    sensor_advice = get_sensor_recommendation(latest_sensor_data)

                    result = {
                        "place": display_name,
                        "state": state,
                        "country": country,
                        "crop": crop,
                        "lat": lat,
                        "lon": lon,
                        "temp": temp,
                        "humidity": humidity,
                        "weather_desc": weather_desc,
                        "wind_speed": wind_speed,
                        "irrigation": irrigation,
                        "disease": disease,
                        "fertilizer": fertilizer,
                        "alert": alert,
                        "sensor_data": latest_sensor_data,
                        "sensor_advice": sensor_advice
                    }

        else:
            error = "Please enter a place or use your current location."

    return render_template("analyzer.html", result=result, error=error)

def chatbot_response(query):
    q = query.lower()

    # -------- detect crop --------
    crop = None
    crops = ["rice", "wheat", "maize", "cotton", "sugarcane"]
    for c in crops:
        if c in q:
            crop = c
            break

    # -------- detect growth stage --------
    stage = None
    if "seed" in q or "sowing" in q or "early" in q:
        stage = "early"
    elif "flower" in q or "flowering" in q:
        stage = "flowering"
    elif "grain" in q or "harvest" in q or "mature" in q:
        stage = "late"

    # -------- detect symptom --------
    symptom = None
    symptom_map = {
        "yellow leaves": "yellow leaves",
        "leaf yellowing": "yellow leaves",
        "spots": "leaf spots",
        "leaf spots": "leaf spots",
        "wilting": "wilting",
        "dry leaves": "dry leaves",
        "fungus": "fungal issue",
        "fungal": "fungal issue",
        "pest": "pest attack",
        "insect": "pest attack",
        "stunted growth": "stunted growth"
    }
    for key, value in symptom_map.items():
        if key in q:
            symptom = value
            break

    # -------- detect weather context --------
    hot_weather = "hot" in q or "high temperature" in q or "heat" in q
    high_humidity = "humidity" in q or "humid" in q
    rain = "rain" in q or "rainfall" in q or "monsoon" in q

    # -------- intent detection --------
    asks_fertilizer = "fertilizer" in q or "manure" in q or "npk" in q or "urea" in q or "dap" in q
    asks_irrigation = "irrigation" in q or "water" in q or "watering" in q
    asks_disease = "disease" in q or "infection" in q or "fungus" in q or "pest" in q or symptom is not None
    asks_soil = "soil" in q or "ph" in q or "nutrient" in q
    asks_weather = "weather" in q or hot_weather or high_humidity or rain

    # -------- crop database --------
    crop_data = {
        "rice": {
            "fertilizer": "Rice usually benefits from nitrogen-rich fertilizer. Split application works better than one heavy dose.",
            "irrigation": "Rice prefers consistent moisture. Keep field moist and avoid unnecessary water overflow.",
            "disease": "Rice is vulnerable to blast and leaf blight in humid conditions. Monitor leaves regularly.",
            "soil": "Rice grows well in fertile, moisture-retentive soil with good nutrient availability."
        },
        "wheat": {
            "fertilizer": "Wheat performs well with balanced NPK and nitrogen support during tillering stage.",
            "irrigation": "Wheat needs moderate irrigation, especially during crown root initiation, flowering, and grain filling.",
            "disease": "Wheat may suffer from rust and blight. Watch for leaf discoloration and patchy infection.",
            "soil": "Wheat prefers well-drained loamy soil with balanced fertility."
        },
        "maize": {
            "fertilizer": "Maize benefits from nitrogen-rich fertilizer during early vegetative growth.",
            "irrigation": "Maize needs timely irrigation, especially during tasseling and grain formation.",
            "disease": "Maize may face leaf blight and stem borer problems. Check leaves and stem condition.",
            "soil": "Maize grows well in fertile, well-drained soil with good organic content."
        },
        "cotton": {
            "fertilizer": "Cotton needs balanced fertilizer with enough potassium for healthy boll development.",
            "irrigation": "Cotton prefers controlled irrigation. Avoid overwatering to reduce root stress.",
            "disease": "Cotton may face boll rot, wilt, and pest attacks. Monitor leaves and bolls carefully.",
            "soil": "Cotton grows best in well-drained black soil or loamy soil."
        },
        "sugarcane": {
            "fertilizer": "Sugarcane requires strong nitrogen support along with balanced nutrients for long growth cycle.",
            "irrigation": "Sugarcane needs regular irrigation, especially during active growth and dry periods.",
            "disease": "Sugarcane can face red rot and fungal issues in poor field conditions.",
            "soil": "Sugarcane prefers fertile, deep, well-drained soil with good moisture holding capacity."
        }
    }

    # -------- symptom advice --------
    symptom_advice = {
        "yellow leaves": "Yellow leaves may indicate nitrogen deficiency, overwatering, poor drainage, or disease. Check whether yellowing starts from older leaves or new leaves.",
        "leaf spots": "Leaf spots often suggest fungal or bacterial infection. Remove badly affected leaves and keep checking spread.",
        "wilting": "Wilting may happen due to low water, root damage, or disease. Check soil moisture first.",
        "dry leaves": "Dry leaves may be caused by heat stress, poor watering, or nutrient imbalance.",
        "fungal issue": "Fungal issues increase in humid weather and poor airflow. Avoid water stagnation and monitor leaf condition.",
        "pest attack": "Pest attack may damage leaves, stems, or roots. Inspect the crop physically for holes, bite marks, or insects.",
        "stunted growth": "Stunted growth may indicate poor soil fertility, root stress, pest damage, or water imbalance."
    }

    # -------- stage advice --------
    stage_advice = {
        "early": "At early growth stage, focus on root establishment, balanced nutrition, and controlled watering.",
        "flowering": "At flowering stage, avoid water stress and nutrient deficiency because yield can be affected.",
        "late": "At late or grain-filling stage, irrigation should be timely but not excessive."
    }

    # -------- weather advice --------
    weather_parts = []
    if hot_weather:
        weather_parts.append("Hot weather increases water demand and can stress crops, so irrigation scheduling becomes more important.")
    if high_humidity:
        weather_parts.append("High humidity raises fungal disease risk, especially if field airflow is poor.")
    if rain:
        weather_parts.append("If rainfall is expected, reduce manual irrigation and ensure proper drainage to avoid waterlogging.")

    # -------- build response --------
    response_parts = []

    if crop and asks_fertilizer:
        response_parts.append(crop_data[crop]["fertilizer"])
    elif crop and asks_irrigation:
        response_parts.append(crop_data[crop]["irrigation"])
    elif crop and asks_disease:
        response_parts.append(crop_data[crop]["disease"])
    elif crop and asks_soil:
        response_parts.append(crop_data[crop]["soil"])

    if symptom:
        response_parts.append(symptom_advice[symptom])

    if stage:
        response_parts.append(stage_advice[stage])

    if weather_parts:
        response_parts.extend(weather_parts)

    # generic crop summary if crop detected but no strong intent
    if crop and not response_parts:
        response_parts.append(
            f"For {crop}, key focus areas are proper irrigation, balanced fertilizer, disease monitoring, and suitable soil condition."
        )

    # generic intent fallback
    if not response_parts:
        if asks_fertilizer:
            response_parts.append("Fertilizer advice depends on crop type, soil condition, and crop stage. Mention the crop for a more precise answer.")
        elif asks_irrigation:
            response_parts.append("Irrigation advice depends on crop type, weather, and growth stage. Mention the crop for a more precise answer.")
        elif asks_disease:
            response_parts.append("Disease advice depends on crop type and symptoms. Mention the crop and visible symptom for better guidance.")
        elif asks_soil:
            response_parts.append("Soil guidance depends on crop and nutrient condition. Mention the crop or soil issue for a better answer.")
        elif asks_weather:
            response_parts.append("Weather affects irrigation demand, disease risk, and crop stress. Mention the crop for specific advice.")
        else:
            response_parts.append(
                "Please ask with more detail like crop name, symptom, weather, or growth stage. Example: 'Yellow leaves in wheat during early growth' or 'Best fertilizer for rice in hot weather?'"
            )

    return " ".join(response_parts)

@app.route("/assistant", methods=["GET", "POST"])
def assistant():
    chat_reply = None

    if request.method == "POST":
        user_query = request.form["chat"]
        chat_reply = chatbot_response(user_query)

    return render_template("assistant.html", chat_reply=chat_reply)

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/alerts")
def alerts():
    sample_alerts = [
        "Low rainfall detected in some regions.",
        "High humidity may increase fungal disease risk.",
        "Efficient irrigation can save water and improve yield."
    ]
    return render_template("alerts.html", alerts=sample_alerts)

@app.route("/sensors", methods=["GET", "POST"])
def sensors():
    global latest_sensor_data
    sensor_advice = []

    if request.method == "POST":
        preset = request.form.get("preset")

        if preset == "dry":
            latest_sensor_data = {
                "soil_moisture": 20,
                "field_temperature": 37,
                "field_humidity": 45,
                "rain_detected": "No",
                "soil_ph": 6.5
            }

        elif preset == "rainy":
            latest_sensor_data = {
                "soil_moisture": 85,
                "field_temperature": 24,
                "field_humidity": 88,
                "rain_detected": "Yes",
                "soil_ph": 6.9
            }

        elif preset == "disease":
            latest_sensor_data = {
                "soil_moisture": 70,
                "field_temperature": 30,
                "field_humidity": 92,
                "rain_detected": "No",
                "soil_ph": 6.7
            }

        elif preset == "healthy":
            latest_sensor_data = {
                "soil_moisture": 50,
                "field_temperature": 28,
                "field_humidity": 65,
                "rain_detected": "No",
                "soil_ph": 6.8
            }

        else:
            latest_sensor_data["soil_moisture"] = request.form["soil_moisture"]
            latest_sensor_data["field_temperature"] = request.form["field_temperature"]
            latest_sensor_data["field_humidity"] = request.form["field_humidity"]
            latest_sensor_data["rain_detected"] = request.form["rain_detected"]
            latest_sensor_data["soil_ph"] = request.form["soil_ph"]

    sensor_advice = get_sensor_recommendation(latest_sensor_data)

    def get_status_classes(sensor_data):
        soil = float(sensor_data["soil_moisture"])
        temp = float(sensor_data["field_temperature"])
        humidity = float(sensor_data["field_humidity"])
        ph = float(sensor_data["soil_ph"])

        return {
            "soil_moisture": "good" if 30 <= soil <= 75 else "bad",
            "field_temperature": "good" if 15 <= temp <= 35 else "warning",
            "field_humidity": "good" if humidity <= 80 else "bad",
            "soil_ph": "good" if 5.5 <= ph <= 8 else "warning",
            "rain_detected": "warning" if sensor_data["rain_detected"] == "Yes" else "good"
        }

    status_classes = get_status_classes(latest_sensor_data)

    return render_template(
        "sensors.html",
        sensor_data=latest_sensor_data,
        sensor_advice=sensor_advice,
        status_classes=status_classes
    )

@app.route("/store")
def store():
    store_catalog = [
        {
            "category": "Pressure Sprayers",
            "summary": "Best for spraying foliar nutrients, pesticides, and water on small garden plots.",
            "items": [
                {
                    "name": "IFFCO Urban Gardens 2L Pressure Sprayer",
                    "site": "Amazon India",
                    "price": 429,
                    "rating": 4.2,
                    "reviews": 78,
                    "trust": 4.7,
                    "tag": "Reliable overall",
                    "notes": "Strong overall balance of trust, usability, and price.",
                    "url": "https://www.amazon.in/IFFCO-Urban-Gardens-Gardening-Multipurpose/dp/B0DFCH33PD"
                },
                {
                    "name": "KisanKraft KK-PS2000 2L Sprayer",
                    "site": "Amazon India",
                    "price": 284,
                    "rating": 3.9,
                    "reviews": 50,
                    "trust": 4.4,
                    "tag": "Budget pick",
                    "notes": "Lowest price option. Good if budget matters most.",
                    "url": "https://www.amazon.in/Kisan-Kraft-KK-PS2000-Manual-Sprayer/dp/B01BLFFE5I"
                },
                {
                    "name": "TrustBasket Premium Pressure Sprayer 2L",
                    "site": "Amazon India",
                    "price": 399,
                    "rating": 4.1,
                    "reviews": 1258,
                    "trust": 4.3,
                    "tag": "Review-heavy",
                    "notes": "Large review volume helps confidence, though quality feedback is mixed.",
                    "url": "https://www.amazon.in/TrustBasket-Premium-Pressure-Sprayer-Gardening/dp/B0CT3J483K"
                }
            ]
        },
        {
            "category": "Watering Cans",
            "summary": "Useful for controlled watering of seedlings, potted crops, and nursery plants.",
            "items": [
                {
                    "name": "Garden Craft 5L Watering Can",
                    "site": "Flipkart",
                    "price": 258,
                    "rating": 4.4,
                    "reviews": 622,
                    "trust": 4.3,
                    "tag": "Best value",
                    "notes": "Best value combination of price and rating.",
                    "url": "https://www.flipkart.com/garden-craft-plastic-watering-can-water-sprayer-sprinkler-plants-indoor-outdoor-gardening-5-litre-with-trowel-l-tank/p/itm5c975b4a6e602"
                },
                {
                    "name": "Jardin 5L Watering Can",
                    "site": "Flipkart",
                    "price": 399,
                    "rating": 4.2,
                    "reviews": 982,
                    "trust": 4.3,
                    "tag": "Popular option",
                    "notes": "More review volume, but noticeably pricier.",
                    "url": "https://www.flipkart.com/jardin-plastic-watering-can-water-sprayer-sprinkler-plants-indoor-outdoor-gardening-5-ltr-l-cane/p/itm7c9abd5bcb762"
                }
            ]
        },
        {
            "category": "Pruning Tools",
            "summary": "For trimming leaves, branches, and plant damage quickly and neatly.",
            "items": [
                {
                    "name": "Sharpex / Urbain Green Bypass Pruner",
                    "site": "Amazon India",
                    "price": 504,
                    "rating": 4.5,
                    "reviews": 62,
                    "trust": 4.4,
                    "tag": "Best rated",
                    "notes": "Highest visible rating in this short list.",
                    "url": "https://www.amazon.in/Heavy-Duty-Pruning-Gardening-Coating-Secateurs/dp/B0DHCW64D4"
                },
                {
                    "name": "IFFCO Urban Gardens Bypass Pruner",
                    "site": "IFFCO Urban Gardens",
                    "price": 499,
                    "rating": 4.0,
                    "reviews": 70,
                    "trust": 4.8,
                    "tag": "Brand-direct",
                    "notes": "Best if you prefer buying directly from an established gardening brand.",
                    "url": "https://iffcourbangardens.com/products/bypass-pruner-heavy-duty"
                }
            ]
        },
        {
            "category": "Organic Fertilizers / Vermicompost",
            "summary": "Good for soil health, steady nutrition, and safer long-term plant feeding.",
            "items": [
                {
                    "name": "IFFCO Urban Gardens Nutri-Rich Vermicompost",
                    "site": "IFFCO Urban Gardens",
                    "price": 899,
                    "rating": 4.76,
                    "reviews": 115,
                    "trust": 4.9,
                    "tag": "Premium organic choice",
                    "notes": "Strong trust score and clearly visible review support from the brand store.",
                    "url": "https://iffcourbangardens.com/products/nutri-rich-seaweed-fortified-vermicompost"
                },
                {
                    "name": "India Gardening Organic Vermicompost",
                    "site": "Amazon India",
                    "price": 499,
                    "rating": 4.2,
                    "reviews": 100,
                    "trust": 4.4,
                    "tag": "Affordable organic",
                    "notes": "Lower entry price and positive review snippet.",
                    "url": "https://www.amazon.in/India-Gardening-Organic-Vermicompost-Fertilizer/dp/B0B4W6YR2Z"
                },
                {
                    "name": "UmaMhaesh Vermicompost 5Kg",
                    "site": "Amazon India",
                    "price": 399,
                    "rating": 3.4,
                    "reviews": 59,
                    "trust": 4.2,
                    "tag": "Budget organic",
                    "notes": "Cheaper, but weaker rating makes it a lower-confidence buy.",
                    "url": "https://www.amazon.in/UmaMhaesh-Organic-Vermicompost-Fertilizer-Gardening/dp/B0DL4CTSGX"
                }
            ]
        },
        {
            "category": "Balanced NPK Fertilizers",
            "summary": "Useful when you want all-round nutrient support rather than a single-nutrient feed.",
            "items": [
                {
                    "name": "Go Garden NPK 19-19-19",
                    "site": "Amazon India",
                    "price": 299,
                    "rating": 4.3,
                    "reviews": 100,
                    "trust": 4.4,
                    "tag": "Best buy",
                    "notes": "Positive review summary and balanced overall value.",
                    "url": "https://www.amazon.in/Go-Garden-19-Fertilizer-Gardening/dp/B0C5JWLJ8P"
                },
                {
                    "name": "SJ Organics NPK 19-19-19",
                    "site": "Amazon India",
                    "price": 349,
                    "rating": 4.2,
                    "reviews": 60,
                    "trust": 4.3,
                    "tag": "Good value",
                    "notes": "Positive quality and value commentary in reviews.",
                    "url": "https://www.amazon.in/Organics-NPK-Fertilizer-Water-Soluble-Flowering/dp/B0FH23L663"
                },
                {
                    "name": "Utkarsh NPK 19-19-19",
                    "site": "Amazon India",
                    "price": 399,
                    "rating": 4.1,
                    "reviews": 50,
                    "trust": 4.4,
                    "tag": "Trusted brand",
                    "notes": "Slightly pricier but still credible for general use.",
                    "url": "https://www.amazon.in/Utkarsh-NPK-Speciality-Crystalline-Fertilizer/dp/B07MQ194LJ"
                }
            ]
        },
        {
            "category": "Seed Bundles",
            "summary": "Useful starter packs for kitchen gardens, balcony farms, and demo seed kits.",
            "items": [
                {
                    "name": "UGAOO Indian Vegetable Seeds Bank",
                    "site": "Amazon India",
                    "price": 199,
                    "rating": 3.8,
                    "reviews": 1026,
                    "trust": 4.5,
                    "tag": "Best value bundle",
                    "notes": "Very attractive price and strong review volume.",
                    "url": "https://www.amazon.in/UGAOO-Indian-Vegetable-Garden-Varieties/dp/B09MLPKZ1T"
                },
                {
                    "name": "UGAOO Indian Vegetable Seeds Bundle",
                    "site": "Flipkart",
                    "price": 399,
                    "rating": 4.0,
                    "reviews": 11,
                    "trust": 4.3,
                    "tag": "Higher-rated listing",
                    "notes": "Higher displayed rating but far fewer reviews than the Amazon listing.",
                    "url": "https://www.flipkart.com/q/vegetable-seeds"
                },
                {
                    "name": "SeedBasket Native Vegetable Combo Pack",
                    "site": "Amazon India",
                    "price": 249,
                    "rating": 4.0,
                    "reviews": 80,
                    "trust": 4.4,
                    "tag": "Native crops combo",
                    "notes": "Good if you want a smaller curated combo instead of a huge bundle.",
                    "url": "https://www.amazon.in/stores/SeedBasket/page/6C20F96C-5CFE-45DB-A74A-4C95C7899207"
                }
            ]
        }
    ]

    # AI-style scoring
    for group in store_catalog:
        prices = [item["price"] for item in group["items"]]
        min_price = min(prices)
        max_price = max(prices)

        for item in group["items"]:
            if max_price == min_price:
                price_score = 5
            else:
                # lower price = higher score
                price_score = 5 - ((item["price"] - min_price) / (max_price - min_price)) * 2

            rating_score = item["rating"]
            review_score = min(item["reviews"] / 300, 1.0) * 5
            trust_score = item["trust"]

            item["ai_score"] = round(
                (price_score * 0.25) +
                (rating_score * 0.35) +
                (review_score * 0.15) +
                (trust_score * 0.25),
                2
            )

        best_name = max(group["items"], key=lambda x: x["ai_score"])["name"]
        for item in group["items"]:
            item["is_best"] = item["name"] == best_name

    return render_template("store.html", store_catalog=store_catalog)

if __name__ == "__main__":
    app.run(debug=True)
