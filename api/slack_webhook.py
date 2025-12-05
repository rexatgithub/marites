from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.github import GitHubClient
from src.slack import SlackClient, SlackWebhookHandler
from src.storage import KVStore
from src.utils import Config, setup_logger, UserManager

logger = setup_logger()
config = Config()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            payload_bytes = self.rfile.read(content_length)
            payload = json.loads(payload_bytes.decode('utf-8'))

            # Handle URL verification challenge first (before signature check)
            if payload.get('type') == 'url_verification':
                logger.info('Responding to Slack URL verification challenge')
                response = {'challenge': payload.get('challenge')}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                return

            # Now verify signature for regular events
            timestamp = self.headers.get('X-Slack-Request-Timestamp', '')
            signature = self.headers.get('X-Slack-Signature', '')

            webhook_handler = SlackWebhookHandler(config.slack_signing_secret)

            if not webhook_handler.verify_signature(timestamp, payload_bytes, signature):
                logger.warning('Invalid Slack signature')
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid signature'}).encode())
                return

            event_data = webhook_handler.parse_event(payload)

            if not event_data:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'Event ignored'}).encode())
                return

            if event_data['type'] == 'command':
                slack_client = SlackClient(config.slack_bot_token)
                kv_store = KVStore(config.kv_rest_api_url, config.kv_rest_api_token)
                user_manager = UserManager(kv_store)

                user_id = event_data['user']
                channel = event_data['channel']
                text = event_data['text'].strip()
                parts = text.split(maxsplit=1)
                command = parts[0].lower()

                if command == 'register':
                    if len(parts) < 2:
                        slack_client.send_dm(user_id, None, '❌ Usage: `register <github_username>`')
                    else:
                        github_username = parts[1].strip()
                        if user_manager.register_user(user_id, github_username):
                            slack_client.send_dm(user_id, None, f'✅ Registered! You will receive PR notifications for GitHub user: `{github_username}`')
                        else:
                            slack_client.send_dm(user_id, None, '❌ Registration failed. Please try again.')

                elif command == 'unregister':
                    if user_manager.unregister_user(user_id):
                        slack_client.send_dm(user_id, None, '✅ Unregistered successfully. You will no longer receive PR notifications.')
                    else:
                        slack_client.send_dm(user_id, None, '❌ You are not registered.')

                elif command == 'status':
                    user_data = user_manager.get_user_by_slack(user_id)
                    if user_data:
                        github_username = user_data.get('github_username', 'Unknown')
                        slack_client.send_dm(user_id, None, f'✅ Registered\n📝 GitHub: `{github_username}`\n💬 Slack: `{user_id}`')
                    else:
                        slack_client.send_dm(user_id, None, '❌ Not registered\n\nSend `register <github_username>` to get started!')

                elif command == 'help':
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
                    slack_client.send_dm(user_id, None, f'❓ Unknown command: `{command}`\n\nSend `help` for available commands.')

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'Command processed'}).encode())
                return

            if event_data['type'] == 'thread_reply':
                github_client = GitHubClient(
                    config.github_app_id,
                    config.github_private_key
                )
                slack_client = SlackClient(config.slack_bot_token)
                kv_store = KVStore(config.kv_rest_api_url, config.kv_rest_api_token)
                user_manager = UserManager(kv_store)

                thread_ts = event_data['thread_ts']
                user_id = event_data['user']
                text = event_data['text']

                # Check if user is registered
                user_data = user_manager.get_user_by_slack(user_id)

                if not user_data:
                    logger.info(f'Ignoring message from unregistered user {user_id}')
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'User not registered'}).encode())
                    return

                logger.info(f'Processing reply from registered user: Slack={user_id}, GitHub={user_data["github_username"]}')

                github_data = kv_store.get_thread_mapping(thread_ts)

                if not github_data:
                    logger.warning(f'No GitHub mapping found for thread {thread_ts}')
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'No GitHub mapping found'}).encode())
                    return

                if github_data['type'] != 'review_comment':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'Not a review comment thread'}).encode())
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
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'message': 'Reply posted to GitHub',
                        'github_comment_id': result['id']
                    }).encode())
                    return

                except Exception as e:
                    logger.error(f'Error posting to GitHub: {e}', exc_info=True)

                    slack_client.add_reaction(
                        event_data['channel'],
                        event_data['ts'],
                        'x'
                    )

                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Failed to post to GitHub'}).encode())
                    return

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'Event processed'}).encode())
            return

        except Exception as e:
            logger.error(f'Error processing Slack webhook: {e}', exc_info=True)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
            return

