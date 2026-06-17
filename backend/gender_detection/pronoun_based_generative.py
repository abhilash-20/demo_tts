import requests

# Ensure your URL includes the endpoint path!
COLAB_API_URL = "https://inspired-quail-partly.ngrok-free.app/get_pronoun_gender"

def generative_pronoun_gender_score(text: str, character: str):
    try:
        payload = {
            "text": text,
            "character": character
        }
        
        # This header is the secret to bypassing the ngrok splash screen
        headers = {
            "ngrok-skip-browser-warning": "69420"
        }
        
        response = requests.post(
            COLAB_API_URL, 
            json=payload, 
            headers=headers, 
            timeout=None  # LLMs take time, so we set a long timeout
        )
        
        # Check if the response is actually JSON
        if response.status_code == 200:
            return response.json()["gender"], response.json()["confidence"]
        else:
            print(f"Server returned error {response.status_code}: {response.text}")
            return "unknown", 0.0
            
    except Exception as e:
        print(f"Error connecting to Colab: {e}")
        return "unknown", 0.0