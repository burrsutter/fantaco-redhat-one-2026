import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Server configuration
    port: int = int(os.getenv("PORT", "8081"))
    host: str = os.getenv("HOST", "0.0.0.0")

    # Model server configuration
    model_server_url: str = os.getenv("MODEL_SERVER_URL", "http://localhost:11434/v1")
    model_name: str = os.getenv("MODEL_NAME", "llama3.2:3b-instruct-fp16")
    api_key: str = os.getenv("API_KEY", "")

    # MCP configuration
    mcp_url: str = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
