import requests

def generate_comic(scenario, file_name, style):
    url = "http://localhost:5000/api/generate_comic"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "scenario": scenario,
        "file_name": file_name,
        "style": style
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Comic strip generated successfully! Strip path: {data['strip_path']}")
        return data['strip_path']
    else:
        print(f"Failed to generate comic. Status code: {response.status_code}, Error: {response.text}")
        return None

# Example usage:
if __name__ == "__main__":
    scenario = "Characters: Lily is a little girl with curly brown hair and a red dress. Max is a small boy with spiky blonde hair and blue overalls. Lily and Max are best friends, and they go to the playground to play on the swings. Lily falls off the swing and Max helps her up. Lily cries and Max comforts her. Lily is happy again."
    file_name = "Lily_and_Max_at_the_playground"
    style = "american comic, colored"

    generate_comic(scenario, file_name, style)
