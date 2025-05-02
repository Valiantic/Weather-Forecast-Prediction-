import requests        
import datetime        
import os               
import numpy as np     
import matplotlib.pyplot as plt                   
from dotenv import load_dotenv
from tabulate import tabulate 

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY") 

# CAVITE 
LAT = 14.4791
LON = 120.8970

end_date = datetime.date.today() - datetime.timedelta(days=1)  
start_date = end_date - datetime.timedelta(days=6)             
today = datetime.date.today()                                  

def get_historical_weather(lat, lon, start, end):
    """Fetch historical weather data for the specified date range and location"""
    url = "https://archive-api.open-meteo.com/v1/archive"  

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min", 
        "timezone": "auto"                               
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        dates = data['daily']['time']           
        temps_max = data['daily']['temperature_2m_max'] 
        temps_min = data['daily']['temperature_2m_min']
        feels_max = data['daily']['apparent_temperature_max']
        feels_min = data['daily']['apparent_temperature_min']
        
        temps_avg = [(max_t + min_t) / 2 for max_t, min_t in zip(temps_max, temps_min)]
        feels_avg = [(max_f + min_f) / 2 for max_f, min_f in zip(feels_max, feels_min)]
        
        return dates, temps_max, temps_min, temps_avg, feels_max, feels_min, feels_avg
    else:
        # Handle API errors
        print("Error:", response.status_code, response.text)
        return [], [], [], [], [], [], []

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
        feels_like = data['main']['feels_like']    
        description = data['weather'][0]['description']  
        return temp, temp_min, temp_max, feels_like, description
    else:
        print("Error fetching today's weather:", response.status_code, response.text)
        return None, None, None, None, None

def display_weather_table(dates, temps_max, temps_min, temps_avg, feels_max, feels_min, feels_avg):
    """Display weather data in a tabular format"""
    table_data = []
    headers = ["Date", "Max Temp (°C)", "Min Temp (°C)", "Avg Temp (°C)", 
               "Max Feels Like (°C)", "Min Feels Like (°C)", "Avg Feels Like (°C)"]
    
    for i, date in enumerate(dates):
        table_data.append([
            date,
            f"{temps_max[i]:.1f}",
            f"{temps_min[i]:.1f}",
            f"{temps_avg[i]:.1f}",
            f"{feels_max[i]:.1f}",
            f"{feels_min[i]:.1f}",
            f"{feels_avg[i]:.1f}"
        ])
    
    print("\n📅 Weather Data for the Past 7 Days:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def visualize_historical_weather(dates, temps_avg, feels_avg):
    """Create visualization for temperature and feels-like temperature"""
    plt.figure(figsize=(12, 7))
    
 
    x_dates = [datetime.datetime.strptime(date, "%Y-%m-%d") for date in dates]
    
    plt.plot(x_dates, temps_avg, 'b-o', linewidth=2, label='Actual Temperature')
    plt.plot(x_dates, feels_avg, 'r-^', linewidth=2, label='Feels Like Temperature')
    
    plt.fill_between(x_dates, temps_avg, feels_avg, color='gray', alpha=0.2)
    
    plt.gcf().autofmt_xdate()
    plt.title("Temperature vs. Feels Like Temperature (Past 7 Days)")
    plt.xlabel("Date")
    plt.ylabel("Temperature (°C)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    for i, (date, temp, feels) in enumerate(zip(x_dates, temps_avg, feels_avg)):
        plt.annotate(f"{temp:.1f}°C", (date, temp), textcoords="offset points", 
                    xytext=(0,10), ha='center')
        plt.annotate(f"{feels:.1f}°C", (date, feels), textcoords="offset points", 
                    xytext=(0,-15), ha='center')
    
    plt.tight_layout()
    plt.show()

def main():
    """Main function to orchestrate the weather data visualization application"""
    # FETCH HISTORICAL WEATHER DATA
    dates, temps_max, temps_min, temps_avg, feels_max, feels_min, feels_avg = get_historical_weather(LAT, LON, start_date, end_date)
    
    # FETCH CURRENT WEATHER DATA TODAY 
    today_temp, today_min, today_max, today_feels, today_desc = get_today_weather(LAT, LON)
    if today_temp is not None:
        print(f"\n📊 Today's Weather ({today.isoformat()}):")
        print(f"Temperature: {today_temp:.2f}°C (Min: {today_min:.2f}°C, Max: {today_max:.2f}°C)")
        print(f"Feels Like: {today_feels:.2f}°C")
        print(f"Condition: {today_desc}")
    
    # DISPLAY WEATHER DATA IN TABLE FORMAT
    display_weather_table(dates, temps_max, temps_min, temps_avg, feels_max, feels_min, feels_avg)
    
    # VISUALIZE HISTORICAL WEATHER DATA
    visualize_historical_weather(dates, temps_avg, feels_avg)

if __name__ == "__main__":
    main()
