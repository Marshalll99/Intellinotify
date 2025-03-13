import requests
import json
import re

def query_ai(prompt):
    """Sends a prompt to AI and returns the response."""
    reqUrl = "http://localhost:11434/api/generate"
    headers = {"Accept": "*/*", "User-Agent": "Chatbot", "Content-Type": "application/json"}

    payload = json.dumps({
        "model": "deepseek-r1:8b",
        "prompt": prompt,
        "stream": False,
        "max_tokens": 8192
    })

    try:
        response = requests.post(reqUrl, data=payload, headers=headers)
        response_json = response.json()

        if "error" in response_json:
            return f"❌ Error: {response_json['error']}"

        raw_response = response_json.get("response", "").strip()
        cleaned_response = re.sub(r"<.*?>", "", raw_response).strip()

        return cleaned_response
    except json.JSONDecodeError:
        return "❌ API returned non-JSON response"
    except requests.exceptions.RequestException as e:
        return f"❌ API request error: {e}"
