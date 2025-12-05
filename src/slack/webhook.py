import hmac
import hashlib
import time
from typing import Dict, Any, Optional


class SlackWebhookHandler:
    def __init__(self, signing_secret: str):
        self.signing_secret = signing_secret

    def verify_signature(self, timestamp: str, body: bytes, signature: str) -> bool:
        if not timestamp or not signature:
            return False

        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False

        sig_basestring = f"v0:{timestamp}:{body.decode()}"
        expected_signature = 'v0=' + hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def parse_event(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        event_type = payload.get('type')

        if event_type == 'url_verification':
            return {
                'type': 'url_verification',
                'challenge': payload.get('challenge')
            }

        if event_type == 'event_callback':
            event = payload.get('event', {})
            event_subtype = event.get('type')

            if event_subtype == 'message':
                if event.get('subtype') or event.get('bot_id'):
                    return None

                thread_ts = event.get('thread_ts')
                channel_type = event.get('channel_type')

                # If it's a thread reply, handle as before
                if thread_ts:
                    return {
                        'type': 'thread_reply',
                        'channel': event.get('channel'),
                        'thread_ts': thread_ts,
                        'user': event.get('user'),
                        'text': event.get('text', ''),
                        'ts': event.get('ts')
                    }

                # If it's a direct message (not in a thread), treat as command
                if channel_type == 'im':
                    return {
                        'type': 'command',
                        'channel': event.get('channel'),
                        'user': event.get('user'),
                        'text': event.get('text', ''),
                        'ts': event.get('ts')
                    }

                return None

        return None

    def parse_interactive(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        payload_type = payload.get('type')

        if payload_type == 'block_actions':
            return {
                'type': 'block_actions',
                'user': payload.get('user', {}).get('id'),
                'actions': payload.get('actions', []),
                'channel': payload.get('channel', {}).get('id'),
                'message_ts': payload.get('message', {}).get('ts')
            }

        return None

