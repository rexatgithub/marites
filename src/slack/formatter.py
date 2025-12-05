from typing import Dict, Any, List
from urllib.parse import quote


class MessageFormatter:
    @staticmethod
    def create_cursor_link(repo_full_name: str, file_path: str, line: int) -> str:
        repo_url = f"https://github.com/{repo_full_name}"
        encoded_repo = quote(repo_url)
        encoded_path = quote(file_path)
        return f"cursor://file/{encoded_repo}/{encoded_path}:{line}"

    @staticmethod
    def format_review_comment(comment_data: Dict[str, Any],
                             code_context: str) -> tuple[List[Dict[str, Any]], str]:
        repo_name = comment_data['repo_name']
        pr_number = comment_data['pr_number']
        pr_title = comment_data['pr_title']
        comment_author = comment_data['comment_author']
        comment_body = comment_data['comment_body']
        comment_url = comment_data['comment_url']
        file_path = comment_data.get('file_path', 'unknown')
        line = comment_data.get('line', 0)
        repo_full_name = comment_data['repo_full_name']

        cursor_link = MessageFormatter.create_cursor_link(
            repo_full_name, file_path, line
        )

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"💬 New Review Comment on PR #{pr_number}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:*\n{repo_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Author:*\n{comment_author}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*PR:*\n<{comment_data['pr_url']}|#{pr_number}: {pr_title}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*File:*\n{file_path}:{line}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Comment:*\n{comment_body}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Code Context:*\n{code_context}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View on GitHub",
                            "emoji": True
                        },
                        "url": comment_url,
                        "action_id": "view_github"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Open in Cursor",
                            "emoji": True
                        },
                        "url": cursor_link,
                        "action_id": "open_cursor"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 _Reply to this thread to respond on GitHub (replies will show as @your_username via Marites)_"
                    }
                ]
            }
        ]

        text = f"New comment from {comment_author} on PR #{pr_number}"

        return blocks, text

    @staticmethod
    def format_review(review_data: Dict[str, Any]) -> tuple[List[Dict[str, Any]], str]:
        repo_name = review_data['repo_name']
        pr_number = review_data['pr_number']
        pr_title = review_data['pr_title']
        review_author = review_data['review_author']
        review_body = review_data['review_body']
        review_url = review_data['review_url']
        review_state = review_data.get('review_state', 'commented')

        emoji_map = {
            'approved': '✅',
            'changes_requested': '🔴',
            'commented': '💬'
        }
        emoji = emoji_map.get(review_state, '💬')

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} New Review on PR #{pr_number}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:*\n{repo_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Reviewer:*\n{review_author}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*PR:*\n<{review_data['pr_url']}|#{pr_number}: {pr_title}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*State:*\n{review_state.replace('_', ' ').title()}"
                    }
                ]
            }
        ]

        if review_body:
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Review Comment:*\n{review_body}"
                    }
                }
            ])

        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View on GitHub",
                        "emoji": True
                    },
                    "url": review_url,
                    "action_id": "view_github_review"
                }
            ]
        })

        text = f"New review from {review_author} on PR #{pr_number}"

        return blocks, text

    @staticmethod
    def format_error(error_message: str) -> tuple[List[Dict[str, Any]], str]:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ *Error:* {error_message}"
                }
            }
        ]
        return blocks, f"Error: {error_message}"

