import hmac
import hashlib
from typing import Dict, Any, Optional


class GitHubWebhookHandler:
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        if not signature:
            return False

        expected_signature = 'sha256=' + hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def parse_review_comment(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        action = payload.get('action')
        if action != 'created':
            return None

        comment = payload.get('comment', {})
        pull_request = payload.get('pull_request', {})
        repository = payload.get('repository', {})
        installation = payload.get('installation', {})

        pr_author = pull_request.get('user', {}).get('login', '')
        comment_author = comment.get('user', {}).get('login', '')

        # Don't notify about self-comments
        if comment_author == pr_author:
            return None

        return {
            'installation_id': installation.get('id'),
            'repo_full_name': repository.get('full_name'),
            'repo_name': repository.get('name'),
            'pr_number': pull_request.get('number'),
            'pr_title': pull_request.get('title'),
            'pr_url': pull_request.get('html_url'),
            'comment_id': comment.get('id'),
            'comment_body': comment.get('body', ''),
            'comment_url': comment.get('html_url'),
            'comment_author': comment_author,
            'file_path': comment.get('path'),
            'diff_hunk': comment.get('diff_hunk', ''),
            'position': comment.get('position'),
            'line': comment.get('line'),
            'commit_id': comment.get('commit_id'),
            'original_position': comment.get('original_position'),
            'original_line': comment.get('original_line'),
        }

    def parse_review(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        action = payload.get('action')
        if action != 'submitted':
            return None

        review = payload.get('review', {})
        if review.get('state') != 'commented' and not review.get('body'):
            return None

        pull_request = payload.get('pull_request', {})
        repository = payload.get('repository', {})
        installation = payload.get('installation', {})

        pr_author = pull_request.get('user', {}).get('login', '')
        review_author = review.get('user', {}).get('login', '')

        # Don't notify about self-reviews
        if review_author == pr_author:
            return None

        return {
            'installation_id': installation.get('id'),
            'repo_full_name': repository.get('full_name'),
            'repo_name': repository.get('name'),
            'pr_number': pull_request.get('number'),
            'pr_title': pull_request.get('title'),
            'pr_url': pull_request.get('html_url'),
            'review_id': review.get('id'),
            'review_body': review.get('body', ''),
            'review_url': review.get('html_url'),
            'review_author': review_author,
            'review_state': review.get('state'),
        }

