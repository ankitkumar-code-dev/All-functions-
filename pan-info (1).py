import requests
import json

url = "https://api.spinny.com/v3/api/vehicle/full-pan-details/"

params = {
  'pan_number': "BBGPP5787F",
  'source': "used-car-loans"
}

payload = {}

headers = {
  'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Mobile Safari/537.36",
  'Accept-Encoding': "gzip, deflate, br, zstd",
  'Content-Type': "application/json",
  'sec-ch-ua-platform': "\"Android\"",
  'sec-ch-ua': "\"Chromium\";v=\"152\", \"Not?A_Brand\";v=\"24\", \"Google Chrome\";v=\"152\"",
  'anonymous-id': "805084276.1789365900",
  'sec-ch-ua-mobile': "?1",
  'platform': "mweb_android",
  'origin': "https://www.spinny.com",
  'sec-fetch-site': "same-site",
  'sec-fetch-mode': "cors",
  'sec-fetch-dest': "empty",
  'referer': "https://www.spinny.com/",
  'accept-language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
  'priority': "u=1, i",
  'Cookie': "_ga=GA1.1.805084276.1789365900; platform=mweb_android; utm_source=direct; varnishPrefixBhpEarly=true; _fbp=fb.1.1789365908705.762646774423246358; _clck=g5c4ud%5E2%5Eg9g%5E0%5E2448; cto_bundle=lG_voV82d0lzUEVIUldlZmFzSUNIJTJGa1BTMjQ4N3NJSllsRzRSNnhnaHFBRU56SDdYZG1hS0MwdGJMamhFQXNzSTd0N1dLJTJCRlRXMHlEUnZmMnFPVnNQTE5kRXVza211cktoajE5JTJCNWxPcUpTS01IUmo4aFN5dTNmV1hxZ29tTlVYMU5Za0FnYU9NeWdqYW4lMkJYTG5KWVFtb0luZyUzRCUzRA; csrftoken=xZUQAkYpTG4PGwW7yWIbQzeBuOAMZ0I0EMGlxqH9edvDaAJaht5pIEUsoRermU2h; sessionid=7l57gfb45f2dd99swehjb1npxagplkg6; _gcl_au=1.1.1317952119.1789365898.-.-.1789367146.936292459.1789367146.1789367163; _clsk=c9oyow%5E1789367170302%5E3%5E1%5Ef.clarity.ms%2Fcollect; _ga_WQREN8TJ7R=GS2.1.s1789365900$o1$g1$t1789367214$j56$l0$h0"
}

response = requests.post(url, params=params, data=json.dumps(payload), headers=headers)

print(response.text)