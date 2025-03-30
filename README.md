# Lemma

Welcome to Lemma! This is a project designed to facilitate code review processes by extracting information from GitHub Pull Request, GitHub Branch or GitHub Commit URLs and generating prompts for feedback. This README provides instructions on how to get started with the app.

![Screenshot 2025-03-30 131819](https://github.com/user-attachments/assets/9458ed49-dd0c-43bd-bc20-b2af27924c7c)


## Prerequisites

Before using the Lemma, ensure that you have the following installed:
- Python 3.x
- `pip install -r requirements.txt`

Environmental Variables:
- GITHUB_ACCESS_TOKEN: Replace <your_github_access_token> with your GitHub access token.
- OPENAI_API_KEY: Replace <your_openai_api_key> with your OpenAI API key.
- ANTHROPIC_API_KEY: Replace <your_anthropic_api_key> with your Anthropic API key.
- DEFAULT_LLM_CLIENT: Set to either openai, ollama or claude.

## Development Setup

If you're planning to contribute to Lemma or run tests, you'll need to set up the development environment:

1. Clone the repository:
   ```
   git clone https://github.com/jdickinsp/lemma.git
   cd lemma
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the project dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install the development and test dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

## Getting Started

To use the Lemma, follow these steps:

1. --url: The URL of the GitHub Pull Request, Branch or Commit to review.
2. [options]: Optional parameters:
  - --prompt_template: Choose a predefined prompt template. Available options are `code-debate`, `code-refactor`, `code-review`, `code-smells`, `code-summary`,     
    `doc-strings`, `doc-markdown`, `explain-lines`, `unit-test` etc.
  - --prompt: Provide a custom prompt for the code review.
  - --per_file: Flag for separate review per file changed.
  - --whole_file: Flag for review of the whole file.
  - --stream_off: Flag for disabling stream mode.
  - --model: Specify if you want to get a specific llm model, such as gpt-4-turbo, gpt-3.5-turbo, llama3, mistral.
  - --client: Specify if you want to get a specific client such as openai, ollama.

Example usage:
```
python cli.py --url=https://github.com/karpathy/llm.c/commit/8cf66fbb845665dabacba992e8a92631132a58d8 --prompt_template=code-review --per_file --client=ollama --model=llama3
```

Run the webapp:
```
python -m streamlit run ./lemma/app.py
```

## Running Test Coverage

To run test coverage for Lemma:

1. Ensure you've completed the Development Setup steps above.

2. Run the tests with coverage:
   ```
   python -m pytest --cov
   ```

This command will run all tests and provide a coverage report in the terminal.

3. For a more detailed HTML coverage report:
   ```
   python -m pytest --cov --cov-report=html
   ```
   This will create a `htmlcov` directory with an `index.html` file that you can open in your browser to view the detailed coverage report.

4. To see which lines of code are not covered by tests:
   ```
   python -m pytest --cov --cov-report=term-missing
   ```
