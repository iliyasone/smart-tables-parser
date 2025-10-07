"""Application configuration helpers."""
import os

EMAIL: str = ""
PASSWORD: str = ""
DEVICE_FINGERPRINT: str = ""
SMART_TABLES_TOKEN: str | None = None

EMAIL = os.getenv("email", EMAIL)
PASSWORD = os.getenv("password", PASSWORD)
DEVICE_FINGERPRINT = os.getenv("device_fingerprint", DEVICE_FINGERPRINT)
SMART_TABLES_TOKEN = os.getenv("token", SMART_TABLES_TOKEN)