# Contributing to AI Story Book

We’re excited that you’re interested in contributing! By helping out, you’ll be making AI-powered storytelling more accessible.


## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Getting Started](#getting-started)
- [Pull Requests](#pull-requests)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Issues and Roadmap](#issues-and-roadmap)
- [License](#license)


<!-- ## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold its terms. -->

## Ways to Contribute

- **Bug Reports**: Found a bug or glitch? Let us know by [opening an issue](https://github.com/YourOrg/ai-story-book/issues).
- **Pull Requests**: Write code to fix bugs or make the model better!

## Getting Started

1. **Fork** the repository and clone it locally.
2. Create a **virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   ```
3. **Install** dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your environment variables.

You can now run:
```bash
uvicorn app.main:app --reload
```
and visit http://127.0.0.1:8000/docs to check that everything works.



## Pull Requests

1. **Branch** off `main` or `dev` (depending on the workflow). Example:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. **Commit** changes:
   - Keep commits small and atomic.
   - Write clear commit messages.
3. **Open** a Pull Request:
   - Clearly describe your changes and link any related issues.
   - If your PR addresses a known issue, reference it (e.g., “Closes #123”).
   - Ensure all CI checks pass (formatting, tests).
4. **Review**:
   - A maintainer will review your code, suggest changes if needed.
   - When approved, your PR will be merged.



## Coding Standards

- **Formatting**: We suggest using [Black](https://github.com/psf/black). You can run:
  ```bash
  black .
  ```
- **Imports**: Sort them logically, typically with [isort](https://github.com/PyCQA/isort).
- **Docstrings**: Use reStructuredText or Google-style docstrings consistently.



## Testing

1. **Add or update** tests in the `tests/` folder.
2. **Run**:
   ```bash
   pytest
   ```
3. **Coverage** is helpful. We encourage aiming for at least 80-90% coverage. Example:
   ```bash
   pytest --cov=app
   ```



## Issues and Roadmap

- Check out our [Issues](https://github.com/YourOrg/ai-story-book/issues) for open tasks.
- See our [Project Board](https://github.com/YourOrg/ai-story-book/projects) (if applicable) for upcoming features.



## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

Thank you for making AI Story Book better! Feel free to ask any questions via [GitHub Issues](https://github.com/YourOrg/ai-story-book/issues).
