import os
from typing import Optional


class Config:
    @staticmethod
    def get(key: str, default: Optional[str] = None) -> str:
        value = os.environ.get(key, default)
        if value is None:
            raise ValueError(f"Missing required environment variable: {key}")
        return value

    @staticmethod
    def get_optional(key: str, default: str = '') -> str:
        return os.environ.get(key, default)

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        value = os.environ.get(key, str(default))
        return value.lower() in ('true', '1', 'yes', 'on')

    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        value = os.environ.get(key, str(default))
        try:
            return int(value)
        except ValueError:
            return default

    @property
    def github_app_id(self) -> str:
        return self.get('GITHUB_APP_ID')

    @property
    def github_private_key(self) -> str:
        key = self.get('GITHUB_PRIVATE_KEY')
        return key.replace('\\n', '\n')

    @property
    def github_webhook_secret(self) -> str:
        return self.get('GITHUB_WEBHOOK_SECRET')

    @property
    def github_username(self) -> str:
        # Legacy - no longer required for multi-user mode
        return self.get_optional('GITHUB_USERNAME', '')

    @property
    def slack_bot_token(self) -> str:
        return self.get('SLACK_BOT_TOKEN')

    @property
    def slack_signing_secret(self) -> str:
        return self.get('SLACK_SIGNING_SECRET')

    @property
    def slack_user_id(self) -> str:
        # Legacy - no longer required for multi-user mode
        return self.get_optional('SLACK_USER_ID', '')

    @property
    def slack_bot_name(self) -> str:
        return self.get_optional('SLACK_BOT_NAME', 'Marites')

    @property
    def kv_rest_api_url(self) -> str:
        return self.get('KV_REST_API_URL')

    @property
    def kv_rest_api_token(self) -> str:
        return self.get('KV_REST_API_TOKEN')

    @property
    def app_secret_key(self) -> str:
        return self.get('APP_SECRET_KEY')

    @property
    def debug(self) -> bool:
        return self.get_bool('DEBUG', False)

