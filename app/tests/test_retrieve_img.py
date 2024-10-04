import requests

def get_comic_image(base_url, user_id, story_title, panel_index, save_path):
    # Construct the URL with query parameters
    url = f"{base_url}/get_comic_image"
    params = {
        'user_id': user_id,
        'story_title': story_title,
        'panel_index': panel_index
    }
    
    # Make the GET request to retrieve the image
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        # Save the image to the specified path
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"Image saved successfully to {save_path}")
    else:
        print(f"Failed to retrieve image. Status code: {response.status_code}, Error: {response.json().get('error')}")

if __name__ == "__main__":
    # Set the base URL of your API
    base_url = "http://localhost:5000/api"  # Update with the actual base URL

    # Specify the parameters
    user_id = "user_test1"
    story_title = "Generated_Story_1"
    panel_index = 0
    save_path = "panel1.png"  # Path where you want to save the image

    # Call the function to retrieve and save the image
    get_comic_image(base_url, user_id, story_title, panel_index, save_path)
