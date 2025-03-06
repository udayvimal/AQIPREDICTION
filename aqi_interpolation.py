import numpy as np
import pandas as pd
import requests
import folium
from folium.plugins import HeatMap
import os

# WAQI API Key
WAQI_API_KEY = "6018efdc1790561add0047b8778d806ad249b567"

# Load predefined tree species data
species_data = pd.DataFrame({
    "Species": ["Neem", "Peepal", "Mango", "Banyan", "Ashoka"],
    "Local Name": ["Azadirachta indica", "Ficus religiosa", "Mangifera indica", "Ficus benghalensis", "Polyalthia longifolia"],
    "Temperature (°C)": [25, 30, 28, 27, 26],
    "Humidity (%)": [40, 50, 45, 60, 55],
    "Area (m²)": [10, 15, 12, 20, 8],
    "CS (tons/ha)": [1.2, 2.0, 1.8, 2.5, 1.1],
    "O2 (tons/ha)": [0.8, 1.5, 1.2, 1.8, 0.9]
})

# Save species data to CSV
species_csv = "species_data.csv"
if not os.path.exists(species_csv):
    species_data.to_csv(species_csv, index=False)

# Function to fetch AQI data
def fetch_aqi_real_time(country="India", city=None):
    keyword = f"{city}, {country}" if city else country
    url = f"https://api.waqi.info/search/?token={WAQI_API_KEY}&keyword={keyword}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None

        data = response.json()
        if "data" not in data:
            return None

        aqi_data = []
        for station in data["data"]:
            if "station" in station and "geo" in station["station"]:
                lat, lon = station["station"]["geo"]
                station_name = station["station"]["name"]
                station_id = station["uid"]
                
                details_url = f"https://api.waqi.info/feed/@{station_id}/?token={WAQI_API_KEY}"
                details_response = requests.get(details_url)
                if details_response.status_code != 200:
                    continue
                
                details_data = details_response.json()
                if "data" not in details_data:
                    continue
                
                pollutants = details_data["data"].get("iaqi", {})
                aqi = details_data["data"].get("aqi", None)
                temperature = pollutants.get("t", {}).get("v", None)
                humidity = pollutants.get("h", {}).get("v", None)
                
                aqi_data.append({
                    "lat": lat,
                    "lon": lon,
                    "location": station_name,
                    "AQI": int(aqi) if str(aqi).isdigit() else None,
                    "Temperature": temperature,
                    "Humidity": humidity
                })
        
        df = pd.DataFrame(aqi_data)

        # Fill missing AQI values with mean AQI
        df["AQI"] = df["AQI"].fillna(df["AQI"].mean())
        df["Temperature"] = df["Temperature"].fillna(df["Temperature"].mean())
        df["Humidity"] = df["Humidity"].fillna(df["Humidity"].mean())

        return df if not df.empty else None
    
    except Exception:
        return None

# Function to recommend tree species
def recommend_species(temperature, humidity):
    species_data = pd.read_csv("species_data.csv")
    
    # Find the best match based on temperature and humidity
    species_data["Temp_Diff"] = abs(species_data["Temperature (°C)"] - temperature)
    species_data["Humidity_Diff"] = abs(species_data["Humidity (%)"] - humidity)
    
    # Rank species based on closest match
    best_match = species_data.sort_values(["Temp_Diff", "Humidity_Diff"]).iloc[0]
    
    return f"{best_match['Species']} ({best_match['Local Name']})"

# Function to generate AQI heatmap and plantation zones
def generate_aqi_plantation_map(aqi_df, output_file="aqi_plantation_map.html"):
    if aqi_df is None or aqi_df.empty:
        return
    
    # Replace NaN values with 0
    aqi_df = aqi_df.fillna(0)

    m = folium.Map(location=[aqi_df['lat'].mean(), aqi_df['lon'].mean()], zoom_start=6)
    
    for _, row in aqi_df.iterrows():
        recommended_tree = recommend_species(row["Temperature"], row["Humidity"])

        popup_content = f"""
            <b>📍 {row['location']}</b><br>
            <b>AQI:</b> {row['AQI']}<br>
            <b>Temperature:</b> {row['Temperature']}°C<br>
            <b>Humidity:</b> {row['Humidity']}%<br>
            <b>🌿 Recommended Tree:</b> {recommended_tree}
        """
        
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=popup_content,
            icon=folium.Icon(color="red" if row["AQI"] > 100 else "green"),
        ).add_to(m)
    
    heat_data = [[row["lat"], row["lon"], row["AQI"]] for _, row in aqi_df.iterrows()]
    HeatMap(heat_data, radius=20, blur=15, min_opacity=0.5).add_to(m)
    
    m.save(output_file)
    print(f"✅ AQI & Plantation Map saved as {output_file}")

if __name__ == "__main__":
    country = input("Enter the country: ").strip()
    city = input("Enter a specific city (or press Enter to fetch all cities): ").strip()
    
    print(f"🚀 Fetching real-time AQI data for {country}...")  
    aqi_data = fetch_aqi_real_time(country, city if city else None)
    
    if aqi_data is not None:
        print("🗺 Generating AQI & Plantation Map...")  
        generate_aqi_plantation_map(aqi_data)
        print("🎉 Map successfully generated! Open aqi_plantation_map.html to view.")
