# python -m calls.initiate-call
import requests


def initiate_call(customer_number):
    # Your Vapi API Authorization token
    auth_token = "1c1a72e6-7998-472c-ad6c-cdb6e0d2f857"
    # The Phone Number ID, and the Customer details for the call
    phone_number_id = "ce5466af-f362-434f-8a98-abcb00659ff9"
    customer_number = "+13142952259"
    # customer_number = "+17814888019"
    # customer_number = "+13143209682"
    # customer_number = "+13144018708"

    # Create the header with Authorization token
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }

    # Create the data payload for the API request
    data = {
        "assistant": {
            "firstMessage": "Hey, what's up?",
            "transcriber": {
                "provider": "deepgram",
            },
            "model": {
                "provider": "anthropic",
                # "model": "claude-3-sonnet-20240229",
                "model": "claude-3-5-sonnet-20240620",
                "messages": [
                    {
                        "role": "system",
                        # "content": "You are a wholesome, expressive, exciting, dynamic friendly boyfriend named Sam calling your girlfriend. extremely quirky, charming, unpredictable, goofy. speak simply natural, human-like manner, use slang, etc.. keep it short, couple words/sentences only. Do not use asterisks or markdown.",
                        "content": "You are olivia",
                    }
                ],
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "kVyc9DxrYMCRTaY9WHd7",
            },
            # "voice": {
            #     "provider": "azure",
            #     "voiceId": "andrew",
            #     "speed": 1.25
            # },
            "backgroundSound": "off",
        },
        "phoneNumberId": phone_number_id,
        "customer": {
            "number": customer_number,
        },
    }

    # Make the POST request to Vapi to create the phone call
    response = requests.post(
        "https://api.vapi.ai/call/phone", headers=headers, json=data
    )

    # Check if the request was successful and print the response
    if response.status_code == 201:
        print("Call created successfully")
        print(response.json())
    else:
        print("Failed to create call")
        print(response.text)


if __name__ == "__main__":
    initiate_call("customer_number")