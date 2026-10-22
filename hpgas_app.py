from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

@app.route('/hp_gas', methods=['GET'])
def get_hp_gas():
    mobile_num = request.args.get('num')
    
    if not mobile_num:
        return jsonify({"error": "Missing 'num' parameter"}), 400

    url = "https://customerapi.hppay.in/api/hppay/lpg/get_consumer_data_from_mobileno_registration"

    payload = {
        "useragent": "402",
        "userip": "2409:40",
        "userid": str(mobile_num),
        "deviceId": "e1bd6744712caafb",
        "deviceOSversion": "36",
        "deviceModel": "samsung",
        "imeiNumber": "hello",
        "appVersion": "5.54",
        "latitude": "0",
        "longitude": "0",
        "mobile_No": str(mobile_num)
    }

    headers = {
        'User-Agent': "okhttp/4.12.0",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Authorization': "Bearer",
        'API_Key': "1BA280E6-BAD6-4AD8-9C2B-6CD5777F517B",
        'Secret_Key': "PVmMSclp834KBIUa9O-XxpBsDJhsi1dsds74CiGaoo5",
        'Content-Type': "application/json; charset=utf-8"
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    