import json
from typing import Dict, Any, List
from multiagenticswarm.utils.logger import get_logger

logger = get_logger(__name__)


class BaseLLM:
    """Abstract LLM interface. Any LLM provider should implement this."""
    async def generate(self, messages: List[Dict[str, str]]) -> str:
        raise NotImplementedError


class PromptParser:
    """LLM-powered parser for natural language collaboration prompts."""

    def __init__(self, llm: BaseLLM, config):
        self.llm = llm
        self.config = config

    def _build_messages(self, prompt: str) -> List[Dict[str, str]]:
        system_content = self.config.system_prompt
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]

    async def parse(self, prompt: str) -> Dict[str, Any]:
        messages = self._build_messages(prompt)
        try:
            logger.info(f"Sending prompt to LLM provider {self.config.provider}")

            response_content = await self.llm.generate(messages)
            response_content = response_content.strip()

            # Clean up possible wrapping artifacts
            if response_content.startswith("json"):
                response_content = response_content[4:].strip()

            result_json = json.loads(response_content)
            logger.info("Prompt parsed successfully")
            return result_json

        except Exception as e:
            logger.error("Prompt parsing failed", extra={"error": str(e), "prompt": prompt})
            raise


# ------------------- Generic Adapters ------------------- #

class OpenAILLM(BaseLLM):
    """Adapter for OpenAI-compatible LLMs (e.g., GPT, LLaMA via OpenAI API)."""
    def __init__(self, api_key: str, model_name: str, base_url: str = None):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    async def generate(self, messages):
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages
        )
        return response.choices[0].message.content


class GroqLLM(OpenAILLM):
    """Adapter for Groq API (inherits OpenAI-compatible API)."""
    def __init__(self, api_key: str, model_name: str):
        # Groq uses same OpenAI-compatible API
        super().__init__(api_key=api_key, model_name=model_name, base_url="https://api.groq.com/openai/v1")
