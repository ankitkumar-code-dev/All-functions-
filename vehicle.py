from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/get_vehicle_info', methods=['GET'])
def get_vehicle_info():
    # User se vehicle number query parameter ke through lena
    # Example: http://127.0.0.1:5000/get_vehicle_info?number=DL10CA1234
    vehicle_number = request.args.get('number')
    
    if not vehicle_number:
        return jsonify({"error": "Vehicle number is required"}), 400

    url = f"https://vehicle.cars24.team/v1/2025-09/vehicle-number/{vehicle_number}"
    
    headers = {
        "sec-ch-ua-platform": "\"Android\"",
        "authorization": "Basic YzJiX2Zyb250ZW5kOko1SXRmQTk2bTJfY3lRVk00dEtOSnBYaFJ0c0NtY1h1",
        "sec-ch-ua": "\"Not:A-Brand\";v=\"99\", \"Google Chrome\";v=\"145\", \"Chromium\";v=\"145\"",
        "sec-ch-ua-mobile": "?1",
        "device_category": "mSite",
        "origin_source": "c2b-website",
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "platform": "rto",
        "origin": "https://www.cars24.com",
        "referer": "https://www.cars24.com/"
    }

    try:
        response = requests.get(url, headers=headers)
        # Agar external API error de toh uska status code aur message return karein
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)