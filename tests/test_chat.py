import requests

API_URL = "http://localhost:4001/chat-story"  # Adjust if your FastAPI server runs on a different port

def chat_loop():
    print("🧙 Welcome to the Story Assistant! (Type 'exit' to quit)")
    while True:
        user_message = input("\nYou: ")
        if user_message.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        response = requests.post(API_URL, json={"message": user_message})

        if response.status_code == 200:
            data = response.json()
            print("\n🤖 Assistant:", data.get("chat_reply"))
            print("📖 Story State Summary:", summarize_state(data.get("story_state")))
        else:
            print("⚠️ Error:", response.status_code, response.text)

def summarize_state(state):
    if not state:
        return "No story started yet."

    summary = []
    if state.get("title"):
        summary.append(f"Title: {state['title']}")
    if state.get("scenario"):
        summary.append(f"Scenario: {state['scenario']}")
    if state.get("entities"):
        summary.append(f"Entities: {len(state['entities'])}")
    if state.get("scenes"):
        summary.append(f"Scenes: {len(state['scenes'])}")

    return " | ".join(summary) if summary else "Empty story state."

if __name__ == "__main__":
    chat_loop()
