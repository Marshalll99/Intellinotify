import requests
import json
import re

def query_ai(prompt):
    """Sends a prompt to AI and returns the response."""
    reqUrl = "http://localhost:11434/api/generate"  # Must have your local AI server running
    headers = {"Accept": "*/*", "User-Agent": "Chatbot", "Content-Type": "application/json"}

    payload = json.dumps({
        "model": "llama3.1",
        "prompt": prompt,
        "stream": False,
        "max_tokens": 8192
    })

    try:
        response = requests.post(reqUrl, data=payload, headers=headers)
        response_json = response.json()

        if "error" in response_json:
            print(f"❌ Error: {response_json['error']}")
            return f"❌ Error: {response_json['error']}"

        raw_response = response_json.get("response", "").strip()
        cleaned_response = re.sub(r"<.*?>", "", raw_response).strip()

        return cleaned_response
    except json.JSONDecodeError:
        print("❌ API returned non-JSON response")
        return "❌ API returned non-JSON response"
    except requests.exceptions.RequestException as e:
        print(f"❌ API request error: {e}")
        return f"❌ API request error: {e}"
