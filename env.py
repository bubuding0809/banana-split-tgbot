from pprint import pprint
from typing import Literal, cast
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv(override=True)  # Override existing environment variables if they exist


class Env(BaseModel):
    ENV: Literal["development", "production", "staging"] = Field(default="development")
    PORT: int = Field(default=8443, description="Port for the Telegram bot to run on")
    TELEGRAM_BOT_TOKEN: str
    MINI_APP_DEEPLINK: str
    API_BASE_URL: str
    API_KEY: str
    TELEGRAM_WEBHOOK_URL: str | None = Field(default=None, description="Optional webhook URL for webhook mode")
    TELEGRAM_WEBHOOK_SECRET: str | None = Field(
        default=None,
        description="Webhook secret for verifying incoming requests when using webhook mode",
    )


# * RUNTIME ENVIRONMENT
_ENV = os.environ.get("ENV", "development")
RunTimeEnvLiteral = Literal["development", "production", "staging"]
VALID_RUNTIME_ENVS = ["development", "production", "staging"]
if _ENV not in VALID_RUNTIME_ENVS:
    raise ValueError(
        f"Invalid ENV value: {_ENV}, must be one of the following: development, production, staging"
    )
_ENV = cast(RunTimeEnvLiteral, _ENV)

# * PORT FOR TELEGRAM BOT
_PORT = os.environ.get("PORT", "8443")
try:
    _PORT = int(_PORT)
except ValueError:
    raise ValueError(f"Invalid PORT value: {_PORT}, must be an integer")

# * TELEGRAM BOT TOKEN FROM BOTFATHER
_TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not _TELEGRAM_BOT_TOKEN:
    raise ValueError(
        "Environment variables not complete: TELEGRAM_BOT_TOKEN is required"
    )

# * BASE URL FOR API SERVICE
_API_BASE_URL = os.environ.get("API_BASE_URL")

if not _API_BASE_URL:
    raise ValueError("Environment variables not complete: API_BASE_URL is required")


# * API KEY FOR API SERVICE AUTHENTICATION
_API_KEY = os.environ.get("API_KEY")
if not _API_KEY:
    raise ValueError("Environment variables not complete: API_KEY is required")


# * TELEGRAM BOT DEEP LINK USED FOR THE MINI APP (e.g. https://t.me/your_bot)
_MINI_APP_DEEPLINK = os.environ.get("MINI_APP_DEEPLINK")
if not _MINI_APP_DEEPLINK:
    raise ValueError(
        "Environment variables not complete: MINI_APP_DEEPLINK is required"
    )

# * WEBHOOK URL FOR TELEGRAM BOT
# This is optional and can be set in the environment variables, but not required for polling mode
_TELEGRAM_WEBHOOK_URL = os.environ.get("TELEGRAM_WEBHOOK_URL")
if _ENV == "production" or _ENV == "staging":
    if not _TELEGRAM_WEBHOOK_URL:
        raise ValueError(
            "Environment variables not complete: TELEGRAM_WEBHOOK_URL is required in production or staging environment"
        )
    
# * WEBHOOK SECRET FOR TELEGRAM BOT
_TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
if _TELEGRAM_WEBHOOK_URL and not _TELEGRAM_WEBHOOK_SECRET:
    raise ValueError(
        "Environment variables not complete: WEBHOOK_SECRET is required when TELEGRAM_WEBHOOK_URL is set"
    )


env = Env(
    ENV=_ENV,
    PORT=_PORT,
    TELEGRAM_BOT_TOKEN=_TELEGRAM_BOT_TOKEN,
    MINI_APP_DEEPLINK=_MINI_APP_DEEPLINK,
    API_BASE_URL=_API_BASE_URL,
    API_KEY=_API_KEY,
    TELEGRAM_WEBHOOK_URL=_TELEGRAM_WEBHOOK_URL,
    TELEGRAM_WEBHOOK_SECRET=_TELEGRAM_WEBHOOK_SECRET,
)

print("[env.py] Environment variables loaded successfully")
print("==============================================")
pprint(env.model_dump())
print("==============================================\n")
