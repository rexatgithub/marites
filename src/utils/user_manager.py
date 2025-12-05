from typing import Optional, Dict
from src.storage import KVStore
from src.utils import setup_logger

logger = setup_logger()


class UserManager:
    def __init__(self, kv_store: KVStore):
        self.kv_store = kv_store

    def register_user(self, slack_user_id: str, github_username: str) -> bool:
        user_data = {
            'github_username': github_username,
            'slack_user_id': slack_user_id,
            'active': True
        }

        if not self.kv_store.save_user_mapping(slack_user_id, user_data):
            logger.error(f'Failed to save Slack ID mapping for {slack_user_id}')
            return False

        if not self.kv_store.save_github_to_slack_mapping(github_username, slack_user_id):
            logger.error(f'Failed to save GitHub username mapping for {github_username}')
            self.kv_store.delete_user_mapping(slack_user_id)
            return False

        logger.info(f'User registered: GitHub={github_username}, Slack={slack_user_id}')
        return True

    def unregister_user(self, slack_user_id: str) -> bool:
        user_data = self.kv_store.get_user_mapping(slack_user_id)
        if not user_data:
            logger.warning(f'Attempted to unregister non-existent user: {slack_user_id}')
            return False

        github_username = user_data.get('github_username')

        if not self.kv_store.delete_user_mapping(slack_user_id):
            logger.error(f'Failed to delete Slack ID mapping for {slack_user_id}')
            return False

        if github_username and not self.kv_store.delete_github_to_slack_mapping(github_username):
            logger.error(f'Failed to delete GitHub username mapping for {github_username}')
            return False

        logger.info(f'User unregistered: GitHub={github_username}, Slack={slack_user_id}')
        return True

    def get_user_by_slack(self, slack_user_id: str) -> Optional[Dict]:
        return self.kv_store.get_user_mapping(slack_user_id)

    def get_user_by_github(self, github_username: str) -> Optional[Dict]:
        slack_user_id = self.kv_store.get_github_to_slack_mapping(github_username)
        if not slack_user_id:
            return None
        return self.kv_store.get_user_mapping(slack_user_id)

    def get_slack_user_id(self, github_username: str) -> Optional[str]:
        return self.kv_store.get_github_to_slack_mapping(github_username)

    def get_github_username(self, slack_user_id: str) -> Optional[str]:
        user_data = self.kv_store.get_user_mapping(slack_user_id)
        return user_data.get('github_username') if user_data else None

    def is_registered(self, slack_user_id: str) -> bool:
        return self.kv_store.get_user_mapping(slack_user_id) is not None
