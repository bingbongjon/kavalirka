from flask import Flask, jsonify, render_template  
import requests  
import json  
from datetime import datetime  
from decouple import config

app = Flask(__name__)  

access_token = config('ACCESS_TOKEN')
url = "https://api.golemio.cz/v2/pid/departureboards"
headers = {"accept": "application/json", "X-Access-Token": access_token}
params = {'ids': 'U240Z1P', 'minutesBefore': 0, 'minutesAfter': 60}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tram_time')
def get_tram_time():
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:

        print(response.text)

        data = json.loads(response.text)
        departures_dict = {}
        
        for departure in data['departures']:
            tram_number = departure['route']['short_name']
            headsign = departure['trip']['headsign']
            departure_time_str = departure['departure_timestamp']['predicted']
            departure_time = datetime.fromisoformat(departure_time_str[:-6])
            current_time = datetime.now()
            time_diff = (departure_time - current_time).seconds // 60
            
            is_wheelchair_accessible = departure['trip'].get('is_wheelchair_accessible', False)
            is_air_conditioned = departure['trip'].get('is_air_conditioned', False)
            
            if tram_number not in departures_dict:
                departures_dict[tram_number] = {'headsign': headsign, 'departures': []}
            
            departures_dict[tram_number]['departures'].append({
                'time_diff': time_diff,
                'is_wheelchair_accessible': is_wheelchair_accessible,
                'is_air_conditioned': is_air_conditioned
            })
            
        return jsonify(departures_dict)
    return jsonify({'error': 'Could not fetch data'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
