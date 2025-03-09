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
- [Docker Deployment](#docker-deployment)
- [Production Setup](#production-setup)
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
2. Click on **Grow Story**
3. Fill in the details and click “Plant & Watch Story Grow” to see your personalized tale.
4. or write a story, add a prompt and click "generate AI Image".


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
3. Access the docs:
   - Open http://127.0.0.1:8000/docs in your browser to see the FastAPI interactive docs.


## Usage

- **Generate Story Text**  
  Endpoint: `POST /generate-story-text`  
  Payload: JSON with scenario, language, entity definitions, etc.  
  This returns a JSON structure containing the story scenes and metadata.

- **Generate Images**  
  Endpoint: `POST /generate-image`  
  Payload: JSON with image prompt, style, and optional entity info.  
  This returns the URL to the generated image.

**Examples** can be found in the [docs/](docs/) folder (e.g., usage guides, advanced configurations).


## Environment Variables

| Variable                | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| `OPENAI_API_KEY`        | API key for OpenAI (for text/image generation if `provider=openai`). |
| `AZURE_OPENAI_API_KEY`  | API key for Azure OpenAI (if `provider=azure`).             |
| `AZURE_OPENAI_ENDPOINT` | Azure endpoint (e.g. `https://example-openai.openai.azure.com`). |
| `PORT`                  | Port to run on (default 4000 in Dockerfile).                |

Check out [`.env.example`](.env.example) for additional placeholders.

---

## Docker Deployment

1. **Build** the image:
   ```bash
   docker build -t txt2story-api .
   ```
2. **Run** the container:
   ```bash
   docker run -p 4000:4000 --env-file .env txt2story-api
   ```
3. Open your browser to http://127.0.0.1:4000 (the default in the Dockerfile).

**Note**: Make sure to pass your environment variables in `.env` or directly through `-e KEY=VALUE`.


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

[AIStorybook.app](https://AIStorybook.app) is maintained by RedApps. Please join our community, file issues, and help us improve this project!
