from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.github import GitHubClient, GitHubWebhookHandler, CodeContextExtractor
from src.slack import SlackClient, MessageFormatter
from src.storage import KVStore
from src.utils import Config, setup_logger, UserManager

logger = setup_logger()
config = Config()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            payload_bytes = self.rfile.read(content_length)

            signature = self.headers.get('X-Hub-Signature-256', '')
            event_type = self.headers.get('X-GitHub-Event', '')

            webhook_handler = GitHubWebhookHandler(config.github_webhook_secret)

            if not webhook_handler.verify_signature(payload_bytes, signature):
                logger.warning('Invalid webhook signature')
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid signature'}).encode())
                return

            payload = json.loads(payload_bytes.decode('utf-8'))

            logger.info(f'Received GitHub webhook: {event_type}')

            if event_type == 'ping':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'pong'}).encode())
                return

            # Early exit: Check if PR author is registered before any processing
            # This avoids unnecessary webhook parsing, KV lookups, and GitHub API calls
            pr_author = payload.get('pull_request', {}).get('user', {}).get('login', '')
            if not pr_author:
                logger.warning('No PR author found in payload, skipping')
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'No PR author'}).encode())
                return

            # Initialize only KV store and user manager for registration check
            kv_store = KVStore(config.kv_rest_api_url, config.kv_rest_api_token)
            user_manager = UserManager(kv_store)

            slack_user_id = user_manager.get_slack_user_id(pr_author)
            if not slack_user_id:
                logger.debug(f'PR author {pr_author} not registered, skipping early')
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'User not registered'}).encode())
                return

            # User is registered, proceed with full processing
            logger.info(f'Processing event for registered user: GitHub={pr_author}, Slack={slack_user_id}')

            github_client = GitHubClient(
                config.github_app_id,
                config.github_private_key
            )
            slack_client = SlackClient(config.slack_bot_token)
            code_extractor = CodeContextExtractor()

            if event_type == 'pull_request_review_comment':
                comment_data = webhook_handler.parse_review_comment(payload)
                if not comment_data:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'Comment ignored'}).encode())
                    return

                comment_id = comment_data['comment_id']
                if kv_store.is_processed('comment', str(comment_id)):
                    logger.info(f'Comment {comment_id} already processed')
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'Already processed'}).encode())
                    return

                logger.info(f'Notifying registered user about new comment')

                installation_id = comment_data['installation_id']
                repo_full_name = comment_data['repo_full_name']
                file_path = comment_data.get('file_path', '')
                commit_id = comment_data.get('commit_id', '')
                line = comment_data.get('line', 0)

                file_content = ''
                if file_path and commit_id:
                    file_content = github_client.get_file_content(
                        installation_id, repo_full_name, file_path, commit_id
                    )

                context = None
                if file_content and line:
                    context = code_extractor.extract_from_file(file_content, line)
                elif comment_data.get('diff_hunk'):
                    context = code_extractor.extract_from_diff(
                        comment_data['diff_hunk'], line
                    )

                code_context = ''
                if context:
                    code_context = code_extractor.format_for_slack(context, file_path)

                blocks, text = MessageFormatter.format_review_comment(
                    comment_data, code_context
                )

                slack_response = slack_client.send_dm(
                    slack_user_id,
                    blocks,
                    text
                )

                if slack_response:
                    thread_ts = slack_response.get('message_ts') or slack_response.get('ts')

                    logger.info(f'Slack response: thread_ts={thread_ts}, channel={slack_response.get("channel")}')

                    comment_saved = kv_store.save_comment_mapping(comment_id, {
                        'channel': slack_response['channel'],
                        'thread_ts': thread_ts,
                        'message_ts': slack_response.get('ts')
                    })

                    thread_saved = kv_store.save_thread_mapping(thread_ts, {
                        'comment_id': comment_id,
                        'installation_id': installation_id,
                        'repo_full_name': repo_full_name,
                        'pr_number': comment_data['pr_number'],
                        'type': 'review_comment'
                    })

                    if not comment_saved or not thread_saved:
                        logger.error(f'KV save failed: comment_saved={comment_saved}, thread_saved={thread_saved}')

                    kv_store.save_last_processed('comment', str(comment_id))

                    logger.info(f'Forwarded comment {comment_id} to Slack (mappings saved: {comment_saved and thread_saved})')
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'Comment forwarded to Slack'}).encode())
                    return
                else:
                    logger.error('Failed to send message to Slack')
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Failed to send to Slack'}).encode())
                    return

            elif event_type == 'pull_request_review':
                review_data = webhook_handler.parse_review(payload)
                if not review_data:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'Review ignored'}).encode())
                    return

                review_id = review_data['review_id']
                if kv_store.is_processed('review', str(review_id)):
                    logger.info(f'Review {review_id} already processed')
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'Already processed'}).encode())
                    return

                logger.info(f'Notifying registered user about new review')

                blocks, text = MessageFormatter.format_review(review_data)

                slack_response = slack_client.send_dm(
                    slack_user_id,
                    blocks,
                    text
                )

                if slack_response:
                    processed_saved = kv_store.save_last_processed('review', str(review_id))
                    logger.info(f'Forwarded review {review_id} to Slack (processed saved: {processed_saved})')
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'message': 'Review forwarded to Slack'}).encode())
                    return
                else:
                    logger.error('Failed to send review to Slack')
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Failed to send to Slack'}).encode())
                    return

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'Event processed'}).encode())
            return

        except Exception as e:
            logger.error(f'Error processing webhook: {e}', exc_info=True)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
            return

