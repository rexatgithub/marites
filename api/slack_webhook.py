from src.utils import Config, setup_logger, UserManager
from src.storage import KVStore
from src.slack import SlackClient, SlackWebhookHandler
from src.github import GitHubClient
from api.webhook_request import WebhookRequest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


logger = setup_logger()
config = Config()


class handler(WebhookRequest):
    EVENT_TYPE_COMMAND = 'command'
    EVENT_TYPE_THREAD_REPLY = 'thread_reply'

    COMMAND_REGISTER = 'register'
    COMMAND_UNREGISTER = 'unregister'
    COMMAND_STATUS = 'status'
    COMMAND_HELP = 'help'

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            payload_bytes = self.rfile.read(content_length)
            payload = json.loads(payload_bytes.decode('utf-8'))

            # Handle URL verification challenge first (before signature check)
            if payload.get('type') == 'url_verification':
                logger.info('Responding to Slack URL verification challenge')
                response = {'challenge': payload.get('challenge')}
                self.response(200, should_log=False, payload=response)
                return

            # Now verify signature for regular events
            timestamp = self.headers.get('X-Slack-Request-Timestamp', '')
            signature = self.headers.get('X-Slack-Signature', '')

            webhook_handler = SlackWebhookHandler(config.slack_signing_secret)

            if not webhook_handler.verify_signature(timestamp, payload_bytes, signature):
                self.response(401, 'Error', 'Invalid signature')
                return

            event_data = webhook_handler.parse_event(payload)

            if not event_data:
                self.response(200, 'Event ignored', should_log=False)
                return

            if event_data['type'] == self.EVENT_TYPE_COMMAND:
                slack_client = SlackClient(config.slack_bot_token)
                kv_store = KVStore(config.kv_rest_api_url,
                                   config.kv_rest_api_token)
                user_manager = UserManager(kv_store)

                user_id = event_data['user']
                channel = event_data['channel']
                text = event_data['text'].strip()
                parts = text.split(maxsplit=1)
                command = parts[0].lower()

                if command == self.COMMAND_REGISTER:
                    if len(parts) < 2:
                        slack_client.send_dm(
                            user_id, None, '❌ Usage: `register <github_username>`')
                    else:
                        github_username = parts[1].strip()
                        if user_manager.register_user(user_id, github_username):
                            slack_client.send_dm(
                                user_id, None, f'✅ Registered! You will receive PR notifications for GitHub user: `{github_username}`')
                        else:
                            slack_client.send_dm(
                                user_id, None, '❌ Registration failed. Please try again.')

                elif command == self.COMMAND_UNREGISTER:
                    if user_manager.unregister_user(user_id):
                        slack_client.send_dm(
                            user_id, None, '✅ Unregistered successfully. You will no longer receive PR notifications.')
                    else:
                        slack_client.send_dm(
                            user_id, None, '❌ You are not registered.')

                elif command == self.COMMAND_STATUS:
                    user_data = user_manager.get_user_by_slack(user_id)
                    if user_data:
                        github_username = user_data.get(
                            'github_username', 'Unknown')
                        slack_client.send_dm(
                            user_id, None, f'✅ Registered\n📝 GitHub: `{github_username}`\n💬 Slack: `{user_id}`')
                    else:
                        slack_client.send_dm(
                            user_id, None, '❌ Not registered\n\nSend `register <github_username>` to get started!')

                elif command == self.COMMAND_HELP:
                    help_text = (
                        '🦜 **PR Marites Commands**\n\n'
                        '• `register <github_username>` - Start receiving PR notifications\n'
                        '• `unregister` - Stop receiving notifications\n'
                        '• `status` - Check your registration status\n'
                        '• `help` - Show this help message\n\n'
                        'After registering, you\'ll receive DMs when someone comments on your PRs!'
                    )
                    slack_client.send_dm(user_id, None, help_text)

                else:
                    slack_client.send_dm(
                        user_id, None, f'❓ Unknown command: `{command}`\n\nSend `help` for available commands.')

                self.response(200, 'Command processed')
                return

            if event_data['type'] == self.EVENT_TYPE_THREAD_REPLY:
                github_client = GitHubClient(
                    config.github_app_id,
                    config.github_private_key
                )
                slack_client = SlackClient(config.slack_bot_token)
                kv_store = KVStore(config.kv_rest_api_url,
                                   config.kv_rest_api_token)
                user_manager = UserManager(kv_store)

                thread_ts = event_data['thread_ts']
                user_id = event_data['user']
                text = event_data['text']

                # Check if user is registered
                user_data = user_manager.get_user_by_slack(user_id)

                if not user_data:
                    self.response(200, 'User not registered', should_log=False)
                    return

                logger.info(
                    f'Processing reply from registered user: Slack={user_id}, GitHub={user_data["github_username"]}')

                github_data = kv_store.get_thread_mapping(thread_ts)

                if not github_data:
                    self.response(200, 'No GitHub mapping found',
                                  should_log=False)
                    return

                if github_data['type'] != 'review_comment':
                    self.response(
                        200, 'Not a review comment thread', should_log=False)
                    return

                installation_id = github_data['installation_id']
                repo_full_name = github_data['repo_full_name']
                comment_id = github_data['comment_id']
                pr_number = github_data['pr_number']

                # Format reply with user attribution
                github_username = user_data['github_username']
                formatted_text = f"**@{github_username}:**\n\n{text}"

                try:
                    result = github_client.post_comment_reply(
                        installation_id,
                        repo_full_name,
                        pr_number,
                        comment_id,
                        formatted_text
                    )

                    slack_client.add_reaction(
                        event_data['channel'],
                        event_data['ts'],
                        'white_check_mark'
                    )

                    logger.info(f'Posted reply to GitHub comment {comment_id}')
                    self.response(200, should_log=False, payload={
                        'message': 'Reply posted to GitHub',
                        'github_comment_id': result['id']
                    })
                    return

                except Exception as e:
                    logger.error(
                        f'Error posting to GitHub: {e}', exc_info=True)

                    slack_client.add_reaction(
                        event_data['channel'],
                        event_data['ts'],
                        'x'
                    )

                    self.response(500, 'Error', 'Failed to post to GitHub')
                    return

            self.response(200, 'Event processed', should_log=False)
            return

        except Exception as e:
            self.response(500, 'Error', str(e))
            return
