import requests
import json
import re

# Function to query AI dynamically
def query_ai(prompt):
    """
    Sends a prompt to DeepSeek-R1 model and returns the AI-generated response.
    
    Args:
        prompt (str): The input prompt to be sent to the AI model.

    Returns:
        str: The cleaned response from the AI model.
    """
    reqUrl = "http://localhost:11434/api/generate"

    headersList = {
        "Accept": "*/*",
        "User-Agent": "Thunder Client (https://www.thunderclient.com)",
        "Content-Type": "application/json"
    }

    payload = json.dumps({
        "model": "deepseek-r1:8b",
        "prompt": prompt,  # Dynamic prompt passed to the function
        "stream": False,
        "max_tokens": 8192
    })

    try:
        response = requests.request("POST", reqUrl, data=payload, headers=headersList)
        response_json = response.json()

        if "error" in response_json:
            return f"❌ Error: {response_json['error']}"

        raw_response = response_json.get("response", "").strip()

        # Remove <think>...</think> and metadata
        cleaned_response = re.sub(r"<.*?>", "", raw_response).strip()

        return cleaned_response  # Return the cleaned AI response

    except json.JSONDecodeError:
        return "❌ API returned non-JSON response"

    except requests.exceptions.RequestException as e:
        return f"❌ API request error: {e}"
