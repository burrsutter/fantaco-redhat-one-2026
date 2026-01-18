"""
vLLM Model Component for Langflow

This component connects to a vLLM server and outputs a LanguageModel
that can be used with Agent components.

"""

from langchain_openai import ChatOpenAI

from langflow.base.models.model import LCModelComponent
from langflow.io import FloatInput, IntInput, MessageInput, Output, SecretStrInput, StrInput
from langflow.schema.message import Message


class VLLMModelComponent(LCModelComponent):
    display_name = "vLLM Model"
    description = "Connects to a vLLM server via OpenAI-compatible API. Use Language Model output for Agents."
    icon = "server"
    name = "VLLMModel"

    inputs = [
        StrInput(
            name="api_base",
            display_name="vLLM API Base URL",
            info="The base URL of your vLLM server (e.g., http://vllm-service:8000/v1)",
            value="http://localhost:8000/v1",
            required=True,
        ),
        StrInput(
            name="model_name",
            display_name="Model Name",
            info="The name of the model served by vLLM",
            value="",
            required=True,
        ),
        SecretStrInput(
            name="api_key",
            display_name="API Key",
            info="API Key for vLLM (use 'EMPTY' if not required)",
            value="EMPTY",
            required=False,
        ),
        FloatInput(
            name="temperature",
            display_name="Temperature",
            info="Controls randomness (0.0 = deterministic, 1.0 = creative)",
            value=0.1,
        ),
        IntInput(
            name="max_tokens",
            display_name="Max Tokens",
            info="Maximum tokens to generate (0 = unlimited)",
            value=4096,
            advanced=True,
        ),
        IntInput(
            name="timeout",
            display_name="Timeout (seconds)",
            info="Request timeout",
            value=120,
            advanced=True,
        ),
        MessageInput(
            name="input_value",
            display_name="Input",
            info="Input message for direct chat (optional)",
            required=False,
        ),
    ]

    outputs = [
        Output(
            display_name="Language Model",
            name="model_output",
            method="build_model",
            types=["LanguageModel"],
            info="Connect this to an Agent's Language Model input",
        ),
        Output(
            display_name="Response",
            name="text_output",
            method="generate_response",
            types=["Message"],
            info="Direct text response (for non-Agent use)",
        ),
    ]

    def build_model(self) -> ChatOpenAI:
        """Build and return the vLLM model as a LangChain ChatOpenAI instance."""
        api_key = self.api_key if self.api_key else "EMPTY"

        model = ChatOpenAI(
            api_key=api_key,
            model=self.model_name,
            base_url=self.api_base,
            temperature=self.temperature,
            max_tokens=self.max_tokens if self.max_tokens > 0 else None,
            timeout=self.timeout,
        )

        return model

    def generate_response(self) -> Message:
        """Generate a response directly (for non-Agent use cases)."""
        if not self.input_value:
            return Message(text="No input provided")

        model = self.build_model()

        # Get the input text
        if hasattr(self.input_value, 'text'):
            input_text = self.input_value.text
        else:
            input_text = str(self.input_value)

        # Generate response
        response = model.invoke(input_text)

        return Message(text=response.content)
