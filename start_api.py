import flask
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import requests
import json
import random

app = Flask(__name__)

#container bookings to simulate VBS 
CONTAINER_BOOKINGS = [
    {
        "container_number": "SEGU1257939",
        "booking_time": "2023-02-12 16:15:00",
        "expected_arrival_time": "2023-02-12 16:15:00",
        "new_expected_arrival_time": None,  # Added new field
        "gate_arrival_time": None,
        "status": "Pending",
        "time_difference": None 
    },
    {
        "container_number": "SSMU2151610",
        "booking_time": "2023-02-17 21:50:23",
        "expected_arrival_time": "2023-02-17 20:57:23",
        "new_expected_arrival_time": None,  # Added new field
        "gate_arrival_time": None,
        "status": "Pending",
        "time_difference": None 
    },
    {
        "container_number": "TSLU3052136",
        "booking_time": "2023-02-21 04:00:48",
        "expected_arrival_time": "2023-02-21 06:00:48",
        "new_expected_arrival_time": None,  # Added new field
        "gate_arrival_time": None,
        "status": "Pending",
        "time_difference": None 
    },
    {
        "container_number": "TRHU3282355",
        "booking_time": "2023-01-14 19:51:18",
        "expected_arrival_time": "2023-01-14 15:51:18",
        "new_expected_arrival_time": None,  # Added new field
        "gate_arrival_time": None,
        "status": "Pending",
        "time_difference": None 
    },
    {
        "container_number": "CAXU8093913",
        "booking_time": "2022-12-03 01:00:00",
        "expected_arrival_time": "2022-12-31 02:23:00",
        "new_expected_arrival_time": None,  # Added new field
        "gate_arrival_time": None,
        "status": "Pending",
        "time_difference": None 
    },
]

def get_auth_token():
    """Get authentication token from ULIP API"""
    url = "https://www.ulipstaging.dpiit.gov.in/ulip/v1.0.0/user/login"
    payload = {
        "username": "docker_usr",
        "password": "docker@28112024"
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get('error') == 'false' and data.get('code') == '200':
            return f"Bearer {data['response']['id']}"
        raise Exception("Authentication failed")
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None

def get_container_info(container_number, auth_token):
    """Get container information from ULIP API"""
    url = "https://www.ulipstaging.dpiit.gov.in/ulip/v1.0.0/LDB/01"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': auth_token
    }
    payload = {"containerNumber": container_number}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Container info error: {str(e)}")
        return None

def extract_container_details(container_data):
    #parse ULP api response data
    try:
        if 'response' in container_data and container_data['response']:
            first_response = container_data['response'][0]
            
            # Get container number
            cntrno = first_response.get('response', {}).get('eximContainerTrail', {}) \
                     .get('cntrDetail', {}).get('cntrno')
            
            # Get last event details
            last_event = first_response.get('response', {}).get('eximContainerTrail', {}) \
                         .get('last_event', [{}])[0]
            
            # Extract all required fields from last_event
            return {
                'cntrno': cntrno,
                'timestamptimezone': last_event.get('timestamptimezone'),
                'eventname': last_event.get('eventname'),
                'currentlocation': last_event.get('currentlocation'),
                'latitude': last_event.get('latitude'),
                'longitude': last_event.get('longitude')
            }
        
        return None
    
    except Exception as e:
        print(f"Error extracting container details: {str(e)}")
        return None

@app.route('/api/update_container_arrival_time/<container_number>', methods=['POST'])
def update_container_arrival_time(container_number):
    """
    Update container's expected_arrival_time using ULIP API and calculate time difference
    """
    # Get authentication token
    auth_token = get_auth_token()
    if not auth_token:
        return jsonify({"error": "Failed to get authentication token"}), 500
    
    # Get container information from ULIP API
    container_data = get_container_info(container_number, auth_token)
    if not container_data:
        return jsonify({"error": "Failed to get container information"}), 404
    
    # Extract container details
    container_details = extract_container_details(container_data)
    if not container_details:
        return jsonify({"error": "Could not extract container details"}), 400
    
    # Find the container in our local storage
    container = next((c for c in CONTAINER_BOOKINGS if c['container_number'] == container_number), None)
    
    if not container:
        return jsonify({"error": "Container not found in local storage"}), 404
    
    if container_details['timestamptimezone']:
        # Store the original expected_arrival_time
        original_expected_time = datetime.fromisoformat(container['expected_arrival_time'])
        
        # Update new_expected_arrival_time
        container['new_expected_arrival_time'] = container_details['timestamptimezone']
        new_expected_time = datetime.fromisoformat(container_details['timestamptimezone'])
        
        # Calculate time difference
        time_diff = (new_expected_time - original_expected_time).total_seconds() / 60  # in minutes
        container['time_difference'] = time_diff
        
        return jsonify({
            "message": "Container arrival time updated successfully",
            "container_number": container_number,
            "new_expected_arrival_time": container['new_expected_arrival_time'],
            "time_difference": container['time_difference']
        }), 200
    
    return jsonify({"error": "No timestamp found in API response"}), 400



    
@app.route('/api/containers', methods=['GET'])
def get_containers():

    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    if not start_time or not end_time:
        return jsonify({"error": "Both start_time and end_time are required"}), 400
    
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO format."}), 400
    
    # Filter containers within the specified time range
    filtered_containers = [
        {
            "container_number": container['container_number'],
            "booking_time": container['booking_time'],
            "expected_arrival_time": container['expected_arrival_time']
        }
        for container in CONTAINER_BOOKINGS
        if (start <= datetime.fromisoformat(container['booking_time']) <= end)
    ]
    
    return jsonify(filtered_containers)

@app.route('/api/container/status/<container_number>', methods=['GET'])
def get_container_status(container_number):
    """
    Get detailed status of a specific container with real-time API data
    
    Checks for delays and current status, including latest expected arrival time from API
    """
    container = next((c for c in CONTAINER_BOOKINGS if c['container_number'] == container_number), None)
    
    if not container:
        return jsonify({"error": "Container not found"}), 404
    
    # Get latest data from API
    auth_token = get_auth_token()
    if not auth_token:
        return jsonify({"error": "Failed to get authentication token"}), 500
    
    container_data = get_container_info(container_number, auth_token)
    if not container_data:
        return jsonify({"error": "Failed to get container information from API"}), 500
    
    # Extract container details including new expected arrival time
    container_details = extract_container_details(container_data)
    if not container_details:
        return jsonify({"error": "Could not extract container details from API response"}), 500
    
    # Get the original expected time
    expected_time = datetime.fromisoformat(container['expected_arrival_time'])
    current_time = datetime.now()
    
    # Get new expected time from API response
    new_expected_time = None
    time_difference = None
    if container_details['timestamptimezone']:
        new_expected_time = container_details['timestamptimezone']
        # Calculate time difference if we have a new expected time
        api_expected_time = datetime.fromisoformat(new_expected_time)
        time_difference = (api_expected_time - expected_time).total_seconds() / 60  # in minutes
    
    # Create status response with API data
    delay_status = {
        "container_number": container_number,
        "booking_time": container['booking_time'],
        "expected_arrival_time": container['expected_arrival_time'],
        "new_expected_arrival_time": new_expected_time,
        "time_difference": time_difference,
        "is_delayed": current_time > expected_time,
        "delay_minutes": max(0, int((current_time - expected_time).total_seconds() / 60)) if current_time > expected_time else 0,
        "status": container['status'],
        "container_details": container_details 
    }
    
    return jsonify(delay_status)


@app.route('/api/ocr/update', methods=['POST'])
def update_container_ocr():
    """
    Update container status from OCR camera input
    """
    data = request.json
    
    if not data or 'container_number' not in data:
        return jsonify({"error": "Container number is required"}), 400
    
    container = next((c for c in CONTAINER_BOOKINGS if c['container_number'] == data['container_number']), None)
    
    if container:
        container['gate_arrival_time'] = datetime.now().isoformat()
        container['status'] = 'Arrived'
        return jsonify({"message": "Container status updated successfully"}), 200
    
    return jsonify({"error": "Container not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)