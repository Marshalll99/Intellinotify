import requests
import json
import re

reqUrl = "http://localhost:11434/api/generate"

headersList = {
    "Accept": "*/*",
    "User-Agent": "Thunder Client (https://www.thunderclient.com)",
    "Content-Type": "application/json"
}

payload = json.dumps({
    "model": "deepseek-r1:8b",
    "prompt": "say, is 3 = 2?",
    "stream": False,
    "max_tokens": 8192
})

response = requests.request("POST", reqUrl, data=payload, headers=headersList)

try:
    response_json = response.json()
    if "error" in response_json:
        print("❌ Error:", response_json["error"])
    else:
        raw_response = response_json.get("response", "")

        # Remove <think>...</think> and other metadata
        cleaned_response = re.sub(r"<.*?>", "", raw_response).strip()

        # Extract only the final answer, removing explanations
        # Keeping only the last few sentences that contain a conclusion
        answer_lines = cleaned_response.split("\n")
        extracted_answer = "\n".join(line for line in answer_lines if "3" in line or "=" in line).strip()

        # Print the clean final answer
        print("✅ Final Answer:", extracted_answer)

except json.JSONDecodeError:
    print("❌ API returned non-JSON:", response.text)
