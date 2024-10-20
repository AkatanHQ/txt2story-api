import requests
import json

# Define the URL of the API endpoint
url = "http://127.0.0.1:5000/api/generate_comic/dall-e-3"
style_description = "Illustration in the style inspired by classic European comic books, specifically reminiscent of Hergé's Tintin. Use clean and consistent black outlines for each character and object, with moderate and uniformly thick lines that emphasize important features without being overpowering. Avoid sketchiness or textured lines, focusing on a polished look. Apply bright and vibrant colors, using primarily reds, blues, greens, and yellows. Color areas should be filled flatly, with no gradients or airbrushed effects. Shading should be minimal and flat, with only one or two tone variations to suggest depth. Character designs should feature expressive yet simplified facial features, ensuring clarity without excess detail. Maintain realistic body proportions—characters should not be exaggerated or caricatured. Use minimal texture, ensuring skin and clothing are uniformly smooth without any visible texture. The overall style should be friendly, visually appealing, and in line with classic comic book aesthetics."

style_description="Belgian comic style featuring clean, uniform lines (ligne claire) with consistent line weight. Use flat, vibrant colors with minimal shading to create a clear and bold look. Characters should have simplified, realistic proportions with slightly stylized features. Detailed but simplified, adding depth without overpowering the characters. The overall atmosphere is adventurous and friendly. Lighting is bright and even, with no complex shadows. The scene should convey a sense of story and clarity, typical of classic European comics like Tintin."

payload = {
	"userId": "user2_testingDetailedDescription",
	"scenario": {
		'description':
			'They are creating a project together. And it will be a success. You can fill in the rest.',
		'characters': [
			{
				'id': 1,
				'name': 'Gabriel',
				'appearance': 'A tall blond guy with glasses',
				'description': '',
				'picture': None
			},
			{
				'id': 2,
				'name': 'Draco',
				'appearance': 'A black short guy with muscles and glasses',
				'description': '',
				'picture': None
			}
		]
	},
    'selectedStyle': 'TINTIN',
    'storyTitle': '',
    'storyLength': 'SHORT',
    'selectedLanguage': 'english'
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
