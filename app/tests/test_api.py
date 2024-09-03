import requests
import json

# Define the URL of the API endpoint
url = "http://127.0.0.1:5000/api/generate_comic"

# Define the payload for the request
payload = {
    "scenario": "Characters: Lily is a little girl with curly brown hair and a red dress. Max is a small boy with spiky blonde hair and blue overalls. Lily and Max are best friends, and they go to the playground to play on the swings. Lily falls off the swing and Max helps her up. Lily cries and Max comforts her. Lily is happy again.",
    "file_name": "Lily_and_Max_at_the_playground",
    "style": "american comic, colored"
}

# Convert the payload to JSON format
headers = {
    'Content-Type': 'application/json'
}

# Send the POST request to the server
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Check the response status code
if response.status_code == 200:
    # Print the success message and the response data
    print("Comic generated successfully!")
    print("Response Data:")
    print(json.dumps(response.json(), indent=4))
else:
    # Print the error message and status code
    print(f"Failed to generate comic. Status code: {response.status_code}")
    print("Response Data:")
    print(json.dumps(response.json(), indent=4))
