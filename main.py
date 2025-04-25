import requests        
import datetime        
import os               
import numpy as np     
from sklearn.linear_model import LinearRegression 
from sklearn.metrics import mean_squared_error    
import matplotlib.pyplot as plt           
import pyttsx3
from dotenv import load_dotenv                    

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY") 

# CAVITE 
LAT = 14.5995
LON = 120.8970

end_date = datetime.date.today() - datetime.timedelta(days=1)  # Yesterday
start_date = end_date - datetime.timedelta(days=6)             # 7 days before yesterday
today = datetime.date.today()      

engine = pyttsx3.init()

def speak(text, rate = 145): #voice speed
    engine.setProperty('rate',rate)
    engine.say(text)
    engine.runAndWait()

def get_historical_weather(lat, lon, start, end):
    """Fetch historical weather data for the specified date range and location"""
    url = "https://archive-api.open-meteo.com/v1/archive"  

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "temperature_2m_max,temperature_2m_min", 
        "timezone": "auto"                               
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:

        data = response.json()
        dates = data['daily']['time']           
        temps_max = data['daily']['temperature_2m_max'] 
        temps_min = data['daily']['temperature_2m_min']  

    
        print(f"\n📅 Weather from {start} to {end}:\n")
        for date, t_max, t_min in zip(dates, temps_max, temps_min):
            print(f"{date}: High {t_max}°C / Low {t_min}°C")
        
        temps_avg = [(max_t + min_t) / 2 for max_t, min_t in zip(temps_max, temps_min)]
        return dates, temps_avg
    else:
        # Handle API errors
        print("Error:", response.status_code, response.text)
        return [], []

def get_today_weather(lat, lon):
    """Fetch current weather data for the specified location"""
    url = "https://api.openweathermap.org/data/2.5/weather"  
    
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,      
        "units": "metric"     
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:

        data = response.json()
        temp = data['main']['temp']           
        temp_min = data['main']['temp_min']    
        temp_max = data['main']['temp_max']    
        description = data['weather'][0]['description']  
        return temp, temp_min, temp_max, description
    else:
        print("Error fetching today's weather:", response.status_code, response.text)
        return None, None, None, None

def predict_next_days(dates, temps):
    """Create a linear regression model to predict temperatures for the next 7 days"""
    
    X = np.arange(len(temps)).reshape(-1, 1)  
    y = np.array(temps)                       
    
    model = LinearRegression()
    model.fit(X, y)
    
    future_days = np.arange(len(temps), len(temps) + 7).reshape(-1, 1)
    predictions = model.predict(future_days)  
    
    y_pred = model.predict(X)                 
    mse = mean_squared_error(y, y_pred)        
    std_error = np.sqrt(mse)                    
    
    conf_interval = (predictions - 2.33 * std_error, predictions + 2.33 * std_error)
    
    return predictions, conf_interval

def plot_next_day_fluctuation(prediction, conf_interval):
    """Visualize hourly temperature fluctuations for the next day"""
    next_day = (end_date + datetime.timedelta(days=1)).isoformat()
    
    hours = np.arange(24)
    
    base_temp = prediction[0]  
    amplitude = abs(conf_interval[1][0] - conf_interval[0][0]) / 4 
    
    hourly_temps = base_temp + amplitude * np.sin((hours - 5) * np.pi / 12)
    
    np.random.seed(42) 
    noise = np.random.normal(0, amplitude/4, 24)
    hourly_temps += noise
    
    hour_labels = [f"{h:02d}:00" for h in hours]
    
    plt.figure(figsize=(12, 6))
    plt.plot(hours, hourly_temps, 'b-o', linewidth=2)
    
    plt.axhline(y=conf_interval[0][0], color='r', linestyle='--', alpha=0.5, 
                label=f"98% Confidence Lower Bound: {conf_interval[0][0]:.2f}°C")
    plt.axhline(y=conf_interval[1][0], color='g', linestyle='--', alpha=0.5,
                label=f"98% Confidence Upper Bound: {conf_interval[1][0]:.2f}°C")
    plt.fill_between(hours, conf_interval[0][0], conf_interval[1][0], 
                    color='gray', alpha=0.2)  
    
    # Format the plot
    plt.xticks(hours[::2], hour_labels[::2], rotation=45)  
    plt.title(f"Predicted Temperature Fluctuations for {next_day}")
    plt.xlabel("Hour of Day")
    plt.ylabel("Temperature (°C)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    plt.text(12, base_temp + 1, f"Base Prediction: {base_temp:.2f}°C", 
             ha='center', va='bottom', bbox=dict(facecolor='white', alpha=0.8))
    
    plt.show()

def generate_weather_description(predictions, today_desc=None):
    """Generate descriptive forecasts based on temperature predictions"""
    descriptions = []
    
    # Temperature thresholds (adjust for your region)
    cold_threshold = 18
    cool_threshold = 24
    warm_threshold = 30
    hot_threshold = 35
    
    # Calculate temperature trends
    trends = []
    for i in range(1, len(predictions)):
        diff = predictions[i] - predictions[i-1]
        if diff > 1.0:
            trends.append("rising")
        elif diff < -1.0:
            trends.append("falling")
        else:
            trends.append("stable")
    trends.insert(0, "initial")  # No trend for first day
    
    # Generate descriptions for each day
    for i, temp in enumerate(predictions):
        temp_desc = ""
        if temp < cold_threshold:
            temp_desc = "cold"
        elif temp < cool_threshold:
            temp_desc = "cool"
        elif temp < warm_threshold:
            temp_desc = "warm"
        elif temp < hot_threshold:
            temp_desc = "hot"
        else:
            temp_desc = "very hot"
            
        trend_text = ""
        if i > 0:
            if trends[i] == "rising":
                trend_text = "warmer than previous day"
            elif trends[i] == "falling":
                trend_text = "cooler than previous day"
            else:
                trend_text = "similar to previous day"
        
        # First day prediction often based on current conditions
        if i == 0 and today_desc:
            conditions = today_desc.lower()
            if "cloud" in conditions:
                forecast = f"Expect {temp_desc} temperatures with continued cloud cover"
            elif "rain" in conditions or "shower" in conditions:
                forecast = f"Expect {temp_desc} temperatures with a chance of continued rain"
            elif "clear" in conditions or "sun" in conditions:
                forecast = f"Expect {temp_desc} temperatures with continued sunshine"
            else:
                forecast = f"Expect {temp_desc} temperatures"
        else:
            if temp_desc in ["hot", "very hot"]:
                forecast = f"Expect a {temp_desc} day, {trend_text}. Stay hydrated and use sun protection"
            elif temp_desc == "warm":
                forecast = f"Expect a pleasant {temp_desc} day, {trend_text}"
            else:
                forecast = f"Expect a {temp_desc} day, {trend_text}. Consider bringing a jacket"
                
        descriptions.append(forecast)
    
    return descriptions

def main():
    """Main function to orchestrate the weather forecast application"""
    # FETCH WEATHER DATA 
    dates, temps = get_historical_weather(LAT, LON, start_date, end_date)
    
    # FETCH CURRENT WEATHER DATA TODAY 
    today_temp, today_min, today_max, today_desc = get_today_weather(LAT, LON)
    if today_temp is not None:
        speak(f"Today's weather is {today_desc} with a temperature of {today_temp:.2f}°C.")
        print(f"\n📊 Today's Weather ({today.isoformat()}):")
        print(f"Temperature: {today_temp:.2f}°C (Min: {today_min:.2f}°C, Max: {today_max:.2f}°C)")
        print(f"Condition: {today_desc}")
    
    # GENERATE PREDICTIONS FOR NEXT 7 DAYS
    predictions, conf_interval = predict_next_days(dates, temps)
    
    # Generate weather descriptions
    weather_descriptions = generate_weather_description(predictions, today_desc)

    # DISPLAY PREDICTIONS WITH CONFIDENCE RATE AND DESCRIPTIONS
    speak("The predicted temperatures for the next 7 days are as follows:")
    print("\n🔮 Predicted Next 7 Days Weather Forecast (with 98% confidence):")
    for i, (temp, description) in enumerate(zip(predictions, weather_descriptions)):
        date = (end_date + datetime.timedelta(days=i+1)).isoformat()
        print(f"{date}: {temp:.2f}°C (± {abs(conf_interval[0][i] - temp):.2f})")
        print(f"   📝 {description}")
        
        # Speak the description for the next day only to avoid too much speech
        if i == 0:
            speak(f"Tomorrow's forecast: {description}")
    
    # Summarize the week trend
    avg_temp = sum(predictions) / len(predictions)
    temp_trend = "warming" if predictions[-1] > predictions[0] else "cooling"
    week_summary = f"\n📅 Weekly Overview: Overall {temp_trend} trend with an average temperature of {avg_temp:.1f}°C"
    print(week_summary)
    speak(f"For the week ahead, expect a {temp_trend} trend with an average temperature of {avg_temp:.1f} degrees Celsius.")

    speak("This is the data visualization temperature prediction for tomorrow")
    plot_next_day_fluctuation(predictions, conf_interval)

if __name__ == "__main__":
    main()
