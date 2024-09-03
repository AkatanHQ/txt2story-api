import requests
import json

# Define the URL of the API endpoint
url = "http://127.0.0.1:5000/api/generate_comic"

# Define the payload for the request
payload = {
    "user_id": "user_124",  # Example user ID
    "scenario": "Characters: John is an adventurous boy with a blue cap and a green backpack. Sarah is a curious girl with long black hair and a yellow jacket. John and Sarah explore a mysterious forest where they discover an ancient tree with glowing leaves. Suddenly, the tree opens up and reveals a hidden pathway leading to an underground cave filled with sparkling crystals.",
    "file_name": "John_and_Sarah_in_the_Forest",
    "style": "american comic, colored",
    "manual_panels": '''[{"number": "1", "description": "A little girl with curly brown hair and a red dress, a small boy with spiky blonde hair and blue overalls, walking together, playground in the background", "text": "Lily: Max, let's go to the playground.\nMax: Yes, let's go play on the swings.", "image_path": "output/Lily_and_Max_at_the_playground/panel-1.png"}, {"number": "2", "description": "The same two children, now on swings, trees and a slide in the background", "text": "Max: Swings are my favourite!\nLily: Me too, Max!", "image_path": "output/Lily_and_Max_at_the_playground/panel-2.png"}, {"number": "3", "description": "The curly haired girl in red dress, falling off the swing, the small boy in blue overalls watching in shock, swing in motion", "text": "Lily: Ahhh!\nMax: Lily!", "image_path": "output/Lily_and_Max_at_the_playground/panel-3.png"}, {"number": "4", "description": "The boy with spiky blonde hair and blue overalls, helping the little girl with curly brown hair and a red dress up, playground equipment in the background", "text": "Max: Lily, are you okay?\nLily: I... I think so.", "image_path": "output/Lily_and_Max_at_the_playground/panel-4.png"}, {"number": "5", "description": "The girl in the red dress, crying, the boy in the blue overalls, comforting her, playground background", "text": "Lily: It hurts, Max!\nMax: It will be okay, Lily.", "image_path": "output/Lily_and_Max_at_the_playground/panel-5.png"}, {"number": "6", "description": "The girl with curly brown hair, smiling again, the boy with spiky blonde hair, relieved, swings and playground in the background", "text": "Lily: I'm okay now, thanks to you Max.\nMax: That's what friends are for, Lily.", "image_path": "output/Lily_and_Max_at_the_playground/panel-6.png"}]'''
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
