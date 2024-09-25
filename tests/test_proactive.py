import requests
from config.config import config

# The ngrok URL you provided
BASE_URL = "https://b251-2601-644-4300-7120-985c-156d-e4e2-a17e.ngrok-free.app"

# The room ID you want to test with
ROOM_ID = "23494025-aa7f-4765-9b1a-0aac89de379f"

# Construct the full URL for the proactive endpoint
url = f"{BASE_URL}/rooms/{ROOM_ID}/proactive"

# Set up the headers with the API key
headers = {"Authorization": f"Bearer {config.BACKEND_API_KEY}"}

try:
    # Make the POST request to the proactive endpoint
    response = requests.post(url, headers=headers)
    
    # Print the status code and content of the response
    print(f"Status Code: {response.status_code}")
    print("Response Content:")
    print(response.text)
    
    # If the response is JSON, you can also print it in a more readable format
    try:
        print("\nJSON Response:")
        print(response.json())
    except requests.exceptions.JSONDecodeError:
        print("\nResponse is not in JSON format.")

except requests.exceptions.RequestException as e:
    print(f"An error occurred while making the request: {e}")