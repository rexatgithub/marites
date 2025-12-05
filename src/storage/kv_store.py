import json
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class KVStore:
    def __init__(self, rest_api_url: str, rest_api_token: str):
        self.base_url = rest_api_url.rstrip('/')
        self.token = rest_api_token
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        logger.info(f"KVStore initialized with URL: {self.base_url}")

    def _get(self, key: str) -> Optional[str]:
        try:
            # Upstash REST API: GET key
            command = ['GET', key]

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=command,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                # Upstash returns the result directly
                result = data.get('result')
                return result
            logger.warning(f"KV GET failed for key {key}: status {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}", exc_info=True)
            return None

    def _set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        try:
            # Upstash REST API expects Redis command format as array
            if ex:
                # SET key value EX seconds
                command = ['SET', key, value, 'EX', str(ex)]
            else:
                # SET key value
                command = ['SET', key, value]

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=command,
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"KV SET successful for key {key}")
                return True
            logger.error(f"KV SET failed for key {key}: status {response.status_code}, body: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}", exc_info=True)
            return False

    def _delete(self, key: str) -> bool:
        try:
            # Upstash REST API: DEL key
            command = ['DEL', key]

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=command,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}", exc_info=True)
            return False

    def save_comment_mapping(self, comment_id: int, slack_data: Dict[str, Any]) -> bool:
        key = f'github_comment:{comment_id}'
        value = json.dumps(slack_data)
        result = self._set(key, value, ex=30*24*60*60)
        if result:
            logger.info(f"Saved comment mapping for {comment_id} -> thread {slack_data.get('thread_ts')}")
        else:
            logger.error(f"Failed to save comment mapping for {comment_id}")
        return result

    def get_comment_mapping(self, comment_id: int) -> Optional[Dict[str, Any]]:
        key = f'github_comment:{comment_id}'
        value = self._get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def save_thread_mapping(self, thread_ts: str, github_data: Dict[str, Any]) -> bool:
        key = f'slack_thread:{thread_ts}'
        value = json.dumps(github_data)
        result = self._set(key, value, ex=30*24*60*60)
        if result:
            logger.info(f"Saved thread mapping for {thread_ts} -> comment {github_data.get('comment_id')}")
        else:
            logger.error(f"Failed to save thread mapping for {thread_ts}")
        return result

    def get_thread_mapping(self, thread_ts: str) -> Optional[Dict[str, Any]]:
        key = f'slack_thread:{thread_ts}'
        value = self._get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def save_last_processed(self, event_type: str, event_id: str) -> bool:
        key = f'last_processed:{event_type}:{event_id}'
        value = datetime.now().isoformat()
        return self._set(key, value, ex=24*60*60)

    def is_processed(self, event_type: str, event_id: str) -> bool:
        key = f'last_processed:{event_type}:{event_id}'
        return self._get(key) is not None

    def save_pr_metadata(self, repo: str, pr_number: int, metadata: Dict[str, Any]) -> bool:
        key = f'pr_metadata:{repo}:{pr_number}'
        value = json.dumps(metadata)
        return self._set(key, value, ex=90*24*60*60)

    def get_pr_metadata(self, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        key = f'pr_metadata:{repo}:{pr_number}'
        value = self._get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def save_user_mapping(self, slack_user_id: str, user_data: Dict[str, Any]) -> bool:
        key = f'user:slack:{slack_user_id}'
        value = json.dumps(user_data)
        return self._set(key, value)

    def get_user_mapping(self, slack_user_id: str) -> Optional[Dict[str, Any]]:
        key = f'user:slack:{slack_user_id}'
        value = self._get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    def delete_user_mapping(self, slack_user_id: str) -> bool:
        key = f'user:slack:{slack_user_id}'
        return self._delete(key)

    def save_github_to_slack_mapping(self, github_username: str, slack_user_id: str) -> bool:
        key = f'user:github:{github_username}'
        return self._set(key, slack_user_id)

    def get_github_to_slack_mapping(self, github_username: str) -> Optional[str]:
        key = f'user:github:{github_username}'
        return self._get(key)

    def delete_github_to_slack_mapping(self, github_username: str) -> bool:
        key = f'user:github:{github_username}'
        return self._delete(key)

