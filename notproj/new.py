import requests
import json

reqUrl = "http://localhost:11434/api/generate"

headersList = {
 "Accept": "*/*",
 "User-Agent": "Thunder Client (https://www.thunderclient.com)",
 "Content-Type": "application/json" 
}

payload = json.dumps({
  "model":"deepseek-r1:8b",
  "prompt":"say, is 3 = 2?",
  "stream":False
})

response = requests.request("POST", reqUrl, data=payload,  headers=headersList)

print(response.text)
