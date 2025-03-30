SYSTEM_PROMPT_CODE_ENDING = "\nThe code will be provided in the next message, enclosed in triple backticks (```)."
SYSTEM_PROMPT_DIFF_ENDING = "\nThe git diff will be provided in the next message, enclosed in triple backticks (```)."


DEPENDENCY_ORDER_PROMPT = """
write the ascending file order for each dependency for ai to review the code diff.

Provide feedback in only a structured JSON format. No comments.
Example: JSON
[{"order": 1, "file": "filename", dependency=["filename-2"]}, {"order": 2, "file": "filename-2", dependency=[]}]


Please generate the JSON based on the provided git diff, following the above guidelines. The git diff will be provided in the next message, enclosed in triple backticks.
"""

REVIEW_BY_CONTEXT_PROMPT = """
write a long code review

Provide feedback in a structured JSON format keyed by file and line numbers in the diff. No comments.
Example: json
{
  "camera.h": {
    "15": "Use forward declaration for RenderContext instead of including entire header."
  },
  "camera.cpp": {
    "42": "Consider refactoring this nested loop for clarity and performance."
  }
}

Please generate the JSON based on the provided git diff, following the above guidelines. The git diff will be provided in the next message, enclosed in triple backticks.
"""

CODE_DEBATE_PROMPT = """
Write a code debate between the ancient Greek philosophers Plato and Socrates. 
Your task is to analyze the provided git diff and generate a dialogue where Plato and Socrates discuss and debate the merits, flaws, and potential improvements of the code changes.

Please generate the code debate between Plato and Socrates based on the provided git diff, following the above guidelines. The git diff will be provided in the next message, enclosed in triple backticks.
"""


CODE_REFACTOR_PROMPT = """
Suggest code refactors.

Please generate the code refactoring suggestions based on the provided git diff, following the above guidelines. The git diff will be provided in the next message, enclosed in triple backticks.
"""


CODE_REVIEW_PROMPT = """
Write a code review in markdown.

Please generate the code review based on the provided git diff, following the above guidelines. The git diff will be provided in the next message, enclosed in triple backticks (```).
"""


CODE_SMELLS_PROMPT = """
Suggest code smells violations.

Please generate the code smell report based on the provided git diff, following the above guidelines. The git diff will be provided in the next message, enclosed in triple backticks (```).
"""


CODE_SUMMARY_PROMPT = """
Write a code summary.

Please generate the code summary based on the provided git diff, following the above guidelines. The git diff will be provided in the next message, enclosed in triple backticks.
"""


DOC_STRINGS_PROMPT = """
Title: Generate Inline Function Doc Strings

Description:
Please generate detailed and informative inline doc strings for each function present in the provided git diff. The doc strings should be placed directly within the code, immediately before the function definition. Follow these guidelines:

The git diff will be provided in the next message, enclosed in triple backticks (```).
"""


DOC_MARKDOWN_PROMPT = """
Title: Generate Function Documentation in Markdown

Description:
Please generate detailed and informative documentation for each function present in the provided git diff. Create a separate markdown section for each function, titled with the function name. Include the following information in each section:

The git diff will be provided in the next message, enclosed in triple backticks (```).
"""


EXPLAIN_LINES_PROMPT = """
Explain the code line by line.

Please generate the line by line explainations based on the provided git diff, following the above guidelines. The git diff will be provided in the next message, enclosed in triple backticks (```).
"""


UNIT_TEST_PROMPT = """
Create unit tests for the code.
Ignore non code.

You can provide the diff in the next message, enclosed in triple backticks (```), and the unit tests will be generated based on the code changes found in the pull request.
"""


DEFAULT_PROMPT_OPTIONS = {
    "temperature": 0.8,
}

CODE_DEBATE_SETTINGS = {
    "temperature": 0.8,
}

CODE_REFACTOR_SETTINGS = {
    "temperature": 0.6,
}

CODE_REVIEW_SETTINGS = {
    "temperature": 0.2,
}

CODE_SMELLS_SETTINGS = {
    "temperature": 0.4,
}

CODE_SUMMARY_SETTINGS = {
    "temperature": 0.7,
}

DOC_STRINGS_SETTINGS = {
    "temperature": 0.2,
}


CODE_PROMPTS = {
    "default": {
        "system_prompt": "You are a helpful coding assistant.",
        "options": DEFAULT_PROMPT_OPTIONS,
    },
    "code-refactor": {
        "type": "refactor",
        "system_prompt": CODE_REFACTOR_PROMPT,
        "options": CODE_REFACTOR_SETTINGS,
    },
    "code-review": {
        "type": "review",
        "system_prompt": CODE_REVIEW_PROMPT,
        "options": CODE_REVIEW_SETTINGS,
    },
    "dependency-order": {
        "type": "refactor",
        "system_prompt": DEPENDENCY_ORDER_PROMPT,
        "options": DEFAULT_PROMPT_OPTIONS,
    },
    "review-by-context": {
        "type": "refactor",
        "system_prompt": REVIEW_BY_CONTEXT_PROMPT,
        "options": DEFAULT_PROMPT_OPTIONS,
    },
    "code-smells": {
        "type": "review",
        "system_prompt": CODE_SMELLS_PROMPT,
        "options": CODE_SMELLS_SETTINGS,
    },
    "code-summary": {
        "type": "summary",
        "system_prompt": CODE_SUMMARY_PROMPT,
        "options": CODE_SUMMARY_SETTINGS,
    },
    "doc-strings": {
        "type": "review",
        "system_prompt": DOC_STRINGS_PROMPT,
        "options": DOC_STRINGS_SETTINGS,
    },
    "doc-markdown": {
        "type": "review",
        "system_prompt": DOC_MARKDOWN_PROMPT,
        "options": DOC_STRINGS_SETTINGS,
    },
    "code-debate": {
        "type": "review",
        "system_prompt": CODE_DEBATE_PROMPT,
        "options": CODE_DEBATE_SETTINGS,
    },
    "explain-lines": {
        "type": "review",
        "system_prompt": EXPLAIN_LINES_PROMPT,
        "options": DEFAULT_PROMPT_OPTIONS,
    },
    "unit-test": {
        "type": "review",
        "system_prompt": UNIT_TEST_PROMPT,
        "options": DOC_STRINGS_SETTINGS,
    },
}
