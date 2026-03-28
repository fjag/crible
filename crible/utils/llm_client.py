"""LLM client wrapper for Anthropic API."""
import time
from typing import Optional
import anthropic


class LLMClientError(Exception):
    """Raised when LLM API call fails."""
    pass


class AnthropicClient:
    """Wrapper for Anthropic API with retry logic and token tracking.

    Attributes:
        client: Anthropic API client instance
        model: Full model ID to use
        token_count: Running total of tokens consumed
    """

    MODEL_MAPPING = {
        "sonnet": "claude-sonnet-4-5-20250929",
        "opus": "claude-opus-4-5-20251101",
        "haiku": "claude-3-5-haiku-20241022",  # Using 3.5 Haiku as 4.5 not available yet
    }

    def __init__(self, api_key: str, model: str = "sonnet"):
        """Initialize the client.

        Args:
            api_key: Anthropic API key
            model: Model shortname or full model ID
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = self._resolve_model_name(model)
        self.token_count = 0

    def _resolve_model_name(self, shortname: str) -> str:
        """Convert shortname to full model ID.

        Args:
            shortname: One of "sonnet", "opus", "haiku", or a full model ID

        Returns:
            Full model ID
        """
        return self.MODEL_MAPPING.get(shortname, shortname)

    def generate(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.0,
        max_retries: int = 3,
    ) -> str:
        """Call Claude API to generate text.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            max_retries: Maximum number of retry attempts for rate limits

        Returns:
            Generated text response

        Raises:
            LLMClientError: If API call fails after retries
        """
        retries = 0
        backoff = 1  # Start with 1 second backoff

        while retries <= max_retries:
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Track token usage
                self.token_count += response.usage.input_tokens + response.usage.output_tokens

                # Extract text from response
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                else:
                    raise LLMClientError("Empty response from API")

            except anthropic.RateLimitError as e:
                retries += 1
                if retries > max_retries:
                    raise LLMClientError(f"Rate limit exceeded after {max_retries} retries: {e}")

                # Exponential backoff
                time.sleep(backoff)
                backoff *= 2

            except anthropic.APIError as e:
                raise LLMClientError(f"API error: {e}")

            except Exception as e:
                raise LLMClientError(f"Unexpected error: {e}")

        raise LLMClientError(f"Failed after {max_retries} retries")

    def get_token_count(self) -> int:
        """Get total tokens consumed so far.

        Returns:
            Total token count
        """
        return self.token_count

    def reset_token_count(self):
        """Reset token counter to zero."""
        self.token_count = 0
