import requests
import json

# Define the URL of the API endpoint
url = "http://127.0.0.1:5000/api/generate_comic"

# Define the payload for the request
payload = {
    "user_id": "user_125",  # Example user ID
    "scenario": "Characters: John is an adventurous boy with a blue cap and a green backpack. Sarah is a curious girl with long black hair and a yellow jacket. John and Sarah explore a mysterious forest where they discover an ancient tree with glowing leaves. Suddenly, the tree opens up and reveals a hidden pathway leading to an underground cave filled with sparkling crystals.",
    "story_title": "John_and_Sarah_in_the_Forest",
    "style": "american comic, colored",
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
    print(json.dumps(response.json(), indent=5))
else:
    # Print the error message and status code
    print(f"Failed to generate comic. Status code: {response.status_code}")
    print("Response Data:")
    print(json.dumps(response.json(), indent=4))
