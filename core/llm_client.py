"""
Groq API client for LLM completions.

Provides a simple complete() interface used by the agent's risk analysis node.
"""

import json
import re
from typing import List

import requests

from config.settings import settings


class OpenRouterClient:
    """HTTP client for the Groq chat completions API.

    Uses Groq's fast inference for risk analysis.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialise with Groq API key.

        Args:
            api_key: Optional override. Defaults to settings.groq_api_key.
        """
        self._key: str = api_key or settings.groq_api_key
        if not self._key:
            raise ValueError(
                "No Groq API key configured. "
                "Set GROQ_API_KEY in your environment."
            )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request to Groq.

        Args:
            system_prompt: Instruction context for the model.
            user_prompt: The user turn content.

        Returns:
            Raw text content from the first assistant message.

        Raises:
            RuntimeError: When the API call fails.
        """
        try:
            response = self._post(self._key, system_prompt, user_prompt)
            response.raise_for_status()
            raw_text = self._extract_text(response.json())
            return self._strip_code_fences(raw_text)
        except requests.RequestException as exc:
            raise RuntimeError(f"Groq API call failed: {exc}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _post(self, api_key: str, system_prompt: str, user_prompt: str) -> requests.Response:
        """Execute the HTTP POST to the Groq completions endpoint.

        Args:
            api_key: Bearer token for authentication.
            system_prompt: System role message content.
            user_prompt: User role message content.

        Returns:
            Raw requests.Response object.
        """
        payload = {
            "model": settings.groq_model,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Making Groq API request to: %s", settings.groq_base_url)
        logger.info("Using model: %s", settings.groq_model)
        
        response = requests.post(
            settings.groq_base_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=120,
        )
        
        if response.status_code != 200:
            logger.error("Groq API error: %d - %s", response.status_code, response.text[:500])
        
        return response

    @staticmethod
    def _extract_text(response_json: dict) -> str:
        """Pull the assistant message text out of the API response.

        Args:
            response_json: Parsed JSON body from the API.

        Returns:
            Text content of the first choice.

        Raises:
            ValueError: If the response shape is unexpected.
        """
        try:
            return response_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ValueError(
                f"Unexpected Groq response shape: {response_json}"
            ) from exc

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Remove markdown code fences that the model may wrap around JSON.

        Args:
            text: Raw model output.

        Returns:
            Cleaned string with fences removed.
        """
        # Remove ```json ... ``` or ``` ... ```
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = cleaned.replace("```", "")
        return cleaned.strip()
