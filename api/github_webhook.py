from src.utils import Config, setup_logger, UserManager
from src.storage import KVStore
from src.slack import SlackClient, MessageFormatter
from src.github import GitHubClient, GitHubWebhookHandler, CodeContextExtractor
from api.webhook_request import WebhookRequest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


logger = setup_logger()
config = Config()


class handler(WebhookRequest):
    PULL_REQUEST_REVIEW_COMMENT = 'pull_request_review_comment'
    PULL_REQUEST_REVIEW = 'pull_request_review'
    PING = 'ping'

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            payload_bytes = self.rfile.read(content_length)

            signature = self.headers.get('X-Hub-Signature-256', '')
            event_type = self.headers.get('X-GitHub-Event', '')

            webhook_handler = GitHubWebhookHandler(
                config.github_webhook_secret)

            if not webhook_handler.verify_signature(payload_bytes, signature):
                self.response(401, 'Error', 'Invalid signature')
                return

            payload = json.loads(payload_bytes.decode('utf-8'))

            logger.info(f'Received GitHub webhook: {event_type}')

            if event_type == self.PING:
                self.response(200, 'pong')
                return

            # Early exit: Check if PR author is registered before any processing
            # This avoids unnecessary webhook parsing, KV lookups, and GitHub API calls
            pr_author = payload.get('pull_request', {}).get(
                'user', {}).get('login', '')

            if not pr_author:
                self.response(200, 'No PR author, skipping')
                return

            # Initialize only KV store and user manager for registration check
            kv_store = KVStore(config.kv_rest_api_url,
                               config.kv_rest_api_token)
            user_manager = UserManager(kv_store)

            slack_user_id = user_manager.get_slack_user_id(pr_author)
            if not slack_user_id:
                self.response(200, 'User not registered, skipping')
                return

            # User is registered, proceed with full processing
            logger.info(
                f'Processing event for registered user: GitHub={pr_author}, Slack={slack_user_id}')

            github_client = GitHubClient(
                config.github_app_id,
                config.github_private_key
            )
            slack_client = SlackClient(config.slack_bot_token)
            code_extractor = CodeContextExtractor()

            if event_type == self.PULL_REQUEST_REVIEW_COMMENT:
                comment_data = webhook_handler.parse_review_comment(payload)
                if not comment_data:
                    self.response(
                        code=200,
                        message='Comment ignored',
                        should_log=False
                    )
                    return

                comment_id = comment_data['comment_id']
                if kv_store.is_processed('comment', str(comment_id)):
                    self.response(
                        200,
                        f'Comment {comment_id} already processed'
                    )
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
                    context = code_extractor.extract_from_file(
                        file_content, line)
                elif comment_data.get('diff_hunk'):
                    context = code_extractor.extract_from_diff(
                        comment_data['diff_hunk'], line
                    )

                code_context = ''
                if context:
                    code_context = code_extractor.format_for_slack(
                        context, file_path)

                blocks, text = MessageFormatter.format_review_comment(
                    comment_data, code_context
                )

                slack_response = slack_client.send_dm(
                    slack_user_id,
                    blocks,
                    text
                )

                if slack_response:
                    thread_ts = slack_response.get(
                        'message_ts') or slack_response.get('ts')

                    logger.info(
                        f'Slack response: thread_ts={thread_ts}, channel={slack_response.get("channel")}')

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
                        logger.error(
                            f'KV save failed: comment_saved={comment_saved}, thread_saved={thread_saved}')

                    kv_store.save_last_processed('comment', str(comment_id))

                    self.response(
                        200,
                        f'Forwarded comment {comment_id} to Slack (mappings saved: {comment_saved and thread_saved})'
                    )
                    return
                else:
                    self.response(
                        500,
                        'Error',
                        'Failed to send to Slack',
                    )
                    return

            elif event_type == self.PULL_REQUEST_REVIEW:
                review_data = webhook_handler.parse_review(payload)
                if not review_data:
                    self.response(
                        200,
                        'Review ignored',
                        should_log=False
                    )
                    return

                review_id = review_data['review_id']
                if kv_store.is_processed('review', str(review_id)):
                    self.response(
                        200,
                        f'Review {review_id} already processed'
                    )
                    return

                logger.info(f'Notifying registered user about new review')

                blocks, text = MessageFormatter.format_review(review_data)

                slack_response = slack_client.send_dm(
                    slack_user_id,
                    blocks,
                    text
                )

                if slack_response:
                    processed_saved = kv_store.save_last_processed(
                        'review', str(review_id))

                    self.response(
                        200,
                        f'Forwarded review {review_id} to Slack (processed saved: {processed_saved})'
                    )
                    return
                else:
                    self.response(
                        500,
                        'Error',
                        'Failed to send to Slack'
                    )
                    return

            self.response(200, 'Event processed', should_log=False)
            return

        except Exception as e:
            self.response(
                500,
                'Error',
                str(e),
            )
            return
