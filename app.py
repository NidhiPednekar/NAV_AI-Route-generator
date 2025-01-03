import folium
from folium.plugins import HeatMap
import requests
from flask import Flask, render_template, request
from folium import PolyLine
import openrouteservice
import herepy

app = Flask(__name__, template_folder='template')

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

@app.route('/', methods=['POST', 'GET'])
def get_map():
    map_html = None
    formatted_duration = ""
    if request.method == 'POST':
        lat1 = float(request.form['lat1'])
        lng1 = float(request.form['lng1'])
        lat2 = float(request.form['lat2'])
        lng2 = float(request.form['lng2'])
        vehicle_type = request.form['vehicle_type']

        url = f"https://data.traffic.hereapi.com/v7/flow?locationReferencing=shape&in=bbox:{lng1},{lat1},{lng2},{lat2}&apiKey=ZhY92oQpAlyZoyMaBp9mI3vFedz_kR9mq0H3M3HhEZY"
        print(url)

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            traffic_data = response.json()

            # Check if 'results' key exists in traffic_data
            if 'results' not in traffic_data:
                return "No traffic data found.", 500

            coordinates = []
            for result in traffic_data['results']:
                if 'location' in result and 'shape' in result['location']:
                    shape = result['location']['shape']
                    for segment in shape.get('segments', []):
                        for point in segment.get('points', []):
                            coordinates.append((point['lat'], point['lng']))

            m = folium.Map(location=[(float(lat1) + float(lat2)) / 2, (float(lng1) + float(lng2)) / 2], zoom_start=14)
            HeatMap(coordinates).add_to(m)
            client = openrouteservice.Client(key='5b3ce3597851110001cf624835a9bfaba5df4c26ad73a754439279b5')  # Replace with your OpenRouteService API key
            coords = [[lng1, lat1], [lng2, lat2]]

            if vehicle_type == 'car':
                profile = 'driving-car'
            elif vehicle_type == 'bicycle':
                profile = 'cycling-regular'
            else:
                profile = 'foot-walking'

            route = client.directions(coordinates=coords, profile=profile, format='geojson')
            duration = route['features'][0]['properties']['segments'][0]['duration']
            folium.GeoJson(route, name='Shortest Path').add_to(m)
            folium.Marker([lat1, lng1], popup='Start', icon=folium.Icon(color='green', icon='play')).add_to(m)
            folium.Marker([lat2, lng2], popup='End', icon=folium.Icon(color='red', icon='stop')).add_to(m)

            map_html = m._repr_html_()
            formatted_duration = format_duration(duration)
            return render_template('index.html', map_html=map_html, duration=formatted_duration)

        except requests.exceptions.RequestException as e:
            return f"Error fetching traffic data: {e}", 500

    return render_template('index.html', map_html=map_html, duration=formatted_duration)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
