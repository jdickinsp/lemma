import abc
import os
import sys
from abc import ABC
from enum import Enum

import ollama
from anthropic import Anthropic, AsyncAnthropic
from openai import AsyncOpenAI, OpenAI

DEFAULT_TEMPERATURE = 0.6


class LLMType(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"


def get_available_models():
    """Return a list of available LLM models."""
    return [
        "o3-mini",  # OpenAI,
        "o1-mini",
        "gpt-4o",
        "claude-3-7-sonnet-latest",
        "claude-3-5-sonnet-latest",  # Anthropic
        "claude-3-5-haiku-latest",
        "llama3.1",  # Ollama
        "llama3.2",
        "deepseek-r1:8b",
        "deepseek-r1:14b",
    ]


def string_to_enum(enum, s):
    try:
        return enum[s.upper()]
    except KeyError:
        raise ValueError(f"No enum member with name '{s}'")


def get_default_llm_model_name(client_type):
    if client_type is LLMType.OPENAI:
        return "o1-mini"
    elif client_type is LLMType.OLLAMA:
        return "llama3.1"
    elif client_type is LLMType.CLAUDE:
        return "claude-3-5-sonnet-latest"
    else:
        raise Exception("not a valid llm client type")


class LLMClient(ABC):
    @abc.abstractmethod
    async def async_chat(self, system_prompt, user_message, prompt_options):
        raise NotImplementedError

    @abc.abstractmethod
    def chat_response(self, system_prompt, user_message, prompt_options):
        raise NotImplementedError

    @abc.abstractmethod
    def stream_chat(self, system_prompt, user_message, prompt_options):
        raise NotImplementedError


class OpenAIClient(LLMClient):
    def __init__(self, model_name):
        api_key = os.getenv("OPENAI_API_KEY")
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    async def async_chat(self, system_prompt, user_message, prompt_options):
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "assistant", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                stream=True,
            )
            return stream
        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            raise

    def chat_response(self, system_prompt, user_message, prompt_options):
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "assistant", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        message = resp.choices[0].message.content.strip()
        return message

    def stream_chat(self, system_prompt, user_message, prompt_options):
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "assistant", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )


class OllamaClient(LLMClient):
    def __init__(self, model_name):
        self.async_client = ollama.AsyncClient()
        self.client = ollama.Client()
        self.model_name = model_name

    def get_messages(self, system_prompt, user_message):
        messages = []
        if "llama" in self.model_name:
            messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ]
        else:
            messages.append(
                {"role": "user", "content": system_prompt + "  \n" + user_message}
            )
        return messages

    async def async_chat(self, system_prompt, user_message, prompt_options):
        try:
            messages = self.get_messages(system_prompt, user_message)
            stream = await self.async_client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": prompt_options["temperature"],
                },
                stream=True,
            )
            return stream
        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            raise

    def chat_response(self, system_prompt, user_message, prompt_options):
        messages = self.get_messages(system_prompt, user_message)
        resp = self.client.chat(
            model=self.model_name,
            messages=messages,
            options={
                "temperature": prompt_options["temperature"],
            },
        )
        message = resp["message"]["content"]
        return message.strip()

    def stream_chat(self, system_prompt, user_message, prompt_options):
        messages = self.get_messages(system_prompt, user_message)
        return self.client.chat(
            model=self.model_name,
            messages=messages,
            options={
                "temperature": prompt_options["temperature"],
            },
            stream=True,
        )


class ClaudeClient(LLMClient):
    def __init__(self, model_name, max_tokens=8192):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.async_client = AsyncAnthropic(api_key=api_key)
        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name
        if "claude-3-haiku" in model_name:
            self.max_tokens = 4096
        else:
            self.max_tokens = max_tokens

    async def async_chat(self, system_prompt, user_message, prompt_options):
        try:
            stream = await self.async_client.messages.create(
                model=self.model_name,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=prompt_options.get("max_tokens", self.max_tokens),
                temperature=prompt_options.get("temperature", DEFAULT_TEMPERATURE),
                stream=True,
            )
            return stream
        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            raise

    def chat_response(self, system_prompt, user_message, prompt_options):
        resp = self.client.messages.create(
            model=self.model_name,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=prompt_options.get("max_tokens", self.max_tokens),
            temperature=prompt_options.get("temperature", DEFAULT_TEMPERATURE),
        )
        return resp.content[0].text

    def stream_chat(self, system_prompt, user_message, prompt_options):
        return self.client.messages.create(
            model=self.model_name,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=prompt_options.get("max_tokens", self.max_tokens),
            temperature=prompt_options.get("temperature", DEFAULT_TEMPERATURE),
            stream=True,
        )
