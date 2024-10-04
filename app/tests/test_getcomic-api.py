import requests
import json

# Define the base URL of the API endpoint
base_url = "http://127.0.0.1:5000/api"

# Function to test /get_user_comics endpoint
def test_get_user_comics():
    url = f"{base_url}/get_user_comics"
    params = {
        'userId': 'user2_testingDetailedDescription'
    }

    # Send the GET request to the server
    response = requests.get(url, params=params)

    # Check the response status code
    if response.status_code == 200:
        # Print the success message and the response data
        print("User comics retrieved successfully!")
        print("Response Data:")
        print(json.dumps(response.json(), indent=5))
    else:
        # Print the error message and status code
        print(f"Failed to retrieve user comics. Status code: {response.status_code}")
        print("Response Data:")
        print(json.dumps(response.json(), indent=4))

# Run the test
if __name__ == "__main__":
    print("Testing /get_user_comics endpoint:")
    test_get_user_comics()
