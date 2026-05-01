"""
config.py – Application configuration loaded from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV: str = os.getenv("APP_ENV", "development")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database/career_finder.db")

# Optional AWS / Bedrock settings (leave blank for local-only mode)
AWS_REGION: str = os.getenv("AWS_REGION", "")
BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "")
AWS_BEARER_TOKEN_BEDROCK: str = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")
