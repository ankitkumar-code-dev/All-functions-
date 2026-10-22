import requests

url = "https://api.vahan.pro/user/searchVehicle"

params = {
  'type': "1",
  'vehicleNumber': "MA3FJEB1S00540102EE",
  'userType': "1"
}

headers = {
  'User-Agent': "okhttp/4.12.0",
  'Connection': "Keep-Alive",
  'Accept': "application/json, text/plain, */*",
  'Accept-Encoding': "gzip",
  'accept-type': "application/json",
  'authorization': "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyVHlwZSI6MywidXNlcklkIjoiNmEzNmFjMzcxNzhiMGMzYjIzOWYxNDc4IiwiaWF0IjoxNzgxOTY3OTI4fQ.WRucn0rozbBZyGvExK3wnrZSxU0ZcAtUaiIBhkzwZ-c",
  'x-api-mobile-key': "MaEHqzXzdWrCEROLWS6TS"
}

response = requests.get(url, params=params, headers=headers)

print(response.text)
