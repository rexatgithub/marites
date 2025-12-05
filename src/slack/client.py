from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Dict, Any, Optional, List


class SlackClient:
    def __init__(self, bot_token: str):
        self.client = WebClient(token=bot_token)
        self._user_cache = {}

    def get_user_id_by_email(self, email: str) -> Optional[str]:
        try:
            response = self.client.users_lookupByEmail(email=email)
            return response['user']['id']
        except SlackApiError:
            return None

    def get_user_dm_channel(self, user_id: str) -> Optional[str]:
        try:
            response = self.client.conversations_open(users=[user_id])
            return response['channel']['id']
        except SlackApiError:
            return None

    def send_dm(self, user_id: str, blocks: List[Dict[str, Any]],
                text: str = '') -> Optional[Dict[str, Any]]:
        try:
            channel_id = self.get_user_dm_channel(user_id)
            if not channel_id:
                return None

            response = self.client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text=text
            )

            return {
                'channel': response['channel'],
                'ts': response['ts'],
                'message_ts': response['ts']
            }
        except SlackApiError as e:
            print(f"Error sending DM: {e}")
            return None

    def send_message(self, channel_id: str, blocks: List[Dict[str, Any]],
                    text: str = '', thread_ts: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            kwargs = {
                'channel': channel_id,
                'blocks': blocks,
                'text': text
            }

            if thread_ts:
                kwargs['thread_ts'] = thread_ts

            response = self.client.chat_postMessage(**kwargs)

            return {
                'channel': response['channel'],
                'ts': response['ts'],
                'thread_ts': response.get('thread_ts', response['ts'])
            }
        except SlackApiError as e:
            print(f"Error sending message: {e}")
            return None

    def get_thread_messages(self, channel_id: str, thread_ts: str) -> List[Dict[str, Any]]:
        try:
            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts
            )

            return response.get('messages', [])
        except SlackApiError:
            return []

    def get_permalink(self, channel_id: str, message_ts: str) -> Optional[str]:
        try:
            response = self.client.chat_getPermalink(
                channel=channel_id,
                message_ts=message_ts
            )
            return response.get('permalink')
        except SlackApiError:
            return None

    def update_message(self, channel_id: str, ts: str,
                      blocks: List[Dict[str, Any]], text: str = '') -> bool:
        try:
            self.client.chat_update(
                channel=channel_id,
                ts=ts,
                blocks=blocks,
                text=text
            )
            return True
        except SlackApiError:
            return False

    def add_reaction(self, channel_id: str, timestamp: str, emoji: str) -> bool:
        try:
            self.client.reactions_add(
                channel=channel_id,
                timestamp=timestamp,
                name=emoji
            )
            return True
        except SlackApiError:
            return False

