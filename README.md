# AI Story Book: The Txt2Story API

The **AI Story Book** project automatically generates personalized storybooks, complete with AI-generated text and images. This repository contains the backend APIs written in Python (FastAPI) that power [AIStorybook.app](https://AIStorybook.app).

---

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Local Development](#local-development)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)
- [Security](#security)
- [Contact](#contact)

---

## Features

- **Automated Story Generation**: Generate short or long story arcs using GPT-based text generation.
- **Image Generation**: Uses Azure or OpenAI image APIs for story illustrations.
- **Extensible**: Entity extraction, multiple style options, and modular architecture.

## Demo

Check out the **live version** at [AIStorybook.app](https://AIStorybook.app).

1. Make an account
2. Buy Story Seeds
3. Click on **Grow Story**
4. Fill in the details and click “Plant & Watch Story Grow” to see your personalized tale.
5. Or write a story, add a prompt, and click "Generate AI Image".

## Getting Started

### Prerequisites
- **Python 3.11+**
- **pip** (or Poetry, Pipenv, etc.)
- An **OpenAI** or **Azure OpenAI** account (API key)
- (Optional) Docker & Docker Compose if you plan to use containers

### Installation

1. **Clone** the repository:
   ```bash
   git clone https://github.com/AkatanHQ/txt2story-api.git
   cd txt2story-api
   ```
2. **Set up a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or on Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Local Development

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Fill in the required environment variables (e.g., `OPENAI_API_KEY` or `AZURE_OPENAI_API_KEY`).
   
2. **Run** the API:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   or  
   ```bash
   python ./run.py
   ```
3. Access the docs:
   - Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser to see the FastAPI interactive docs.

## Usage  

- **Generate Story Text**  
  Endpoint: `POST /generate-story-text`  
  Payload: JSON with scenario, entity definitions, etc.  
  This returns a JSON structure containing the story scenes and metadata.  

- **Generate Images**  
  Endpoint: `POST /generate-image`  
  Payload: JSON with image prompt, style, and optional entity info.  
  This returns the URL to the generated image.  

- **Analyze Image from URL**   
  Endpoint: `POST /analyze-image-url`  
  Payload: JSON with an image URL, provider, and vision model.  
  This returns a JSON object with a detailed description of the image.  

- **Analyze Base64 Image**   
  Endpoint: `POST /analyze-image-base64`  
  Payload: JSON with a base64-encoded image, provider, and vision model.  
  This returns a JSON object with a detailed description of the image.  

<details>
  <summary><strong>📖 Usage in Detail (Click to Expand)</strong></summary>

### Generate Story Text  
**Endpoint**: `POST /generate-story-text`  
**Payload**:  
```json
{
  "entities": [
    {
      "name": "Alice",
      "role": "protagonist",
      "description": "A curious young girl with long brown hair and a red dress."
    }
  ],
  "number_of_pages": 5,
  "scenario": "Alice finds a magical portal in her backyard."
}
```  
**Response**:  
```json
{
  "metadata": {
    "title": "Alice's Magical Adventure",
    "genre": "Fantasy",
    "keywords": ["Magic", "Adventure", "Portal"]
  },
  "scenes": [
    {
      "index": 0,
      "text": "Alice discovers a glowing portal in her backyard.",
      "image": {
        "prompt": "A young girl in a red dress looking at a glowing portal.",
        "url": "",
        "signed_url": ""
      }
    }
  ],
  "entities": [
    {
      "name": "Alice",
      "detailed_appearance": "A young girl with long brown hair, wearing a red dress."
    }
  ]
}
```  

### Generate Images  
**Endpoint**: `POST /generate-image`  
**Payload**:  
```json
{
  "image_prompt": "A knight standing on a hill under a stormy sky.",
  "style": "realistic",
  "provider": "openai",
  "image_model": "dall-e-3",
  "model_resolution": "1024x1024",
  "entities": [
    {
      "name": "Knight",
      "description": "A warrior in shining armor with a large sword."
    }
  ]
}
```  
**Response**:  
```json
{
  "image_url": "https://generated-image.com/example.jpg"
}
```  

### Analyze Image from URL  
**Endpoint**: `POST /analyze-image-url`  
**Payload**:  
```json
{
  "image_url": "https://example.com/image.jpg",
  "provider": "openai",
  "vision_model": "gpt-4o"
}
```  
**Response**:  
```json
{
  "detailed_appearance": "A person with short brown hair, wearing a blue jacket, looking happy."
}
```  

### Analyze Base64 Image  
**Endpoint**: `POST /analyze-image-base64`  
**Payload**:  
```json
{
  "image_base64": "<base64_string>",
  "provider": "openai",
  "vision_model": "gpt-4o"
}
```  
**Response**:  
```json
{
  "detailed_appearance": "A woman with long black hair, wearing a red dress, smiling."
}
```  

</details>

## Environment Variables

| Variable                | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| `OPENAI_API_KEY`        | API key for OpenAI (for text/image generation if `provider=openai`). |
| `AZURE_OPENAI_API_KEY`  | API key for Azure OpenAI (if `provider=azure`).             |
| `AZURE_OPENAI_ENDPOINT` | Azure endpoint (e.g. `https://example-openai.openai.azure.com`). |

Check out [`.env.example`](.env.example) for additional placeholders.

---

## Contributing

We **welcome** contributions! Check out [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

## License

This project is licensed under the terms of the [MIT License](./LICENSE).

## Security

If you discover any security issues, please review our [SECURITY.md](SECURITY.md) for how to report vulnerabilities. We appreciate your help!

## Contact

**Project Maintainers**:  
- AI Story Book (<hello@aistorybook.app>)  
- Or open an issue on [GitHub](https://github.com/AkatanHQ/txt2story-api)

[AIStorybook.app](https://AIStorybook.app) is maintained by Akatan. Please join our community, file issues, and help us improve this project!