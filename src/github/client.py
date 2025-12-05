import jwt
import time
import requests
from typing import Optional, Dict, Any
from github import Github, GithubIntegration, Auth


class GitHubClient:
    def __init__(self, app_id: str, private_key: str):
        self.app_id = app_id
        self.private_key = private_key
        self._installation_tokens = {}

    def _generate_jwt(self) -> str:
        payload = {
            'iat': int(time.time()),
            'exp': int(time.time()) + (10 * 60),
            'iss': self.app_id
        }
        return jwt.encode(payload, self.private_key, algorithm='RS256')

    def _get_installation_token(self, installation_id: int) -> str:
        cached = self._installation_tokens.get(installation_id)
        if cached and cached['expires_at'] > time.time() + 60:
            return cached['token']

        jwt_token = self._generate_jwt()
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
        response = requests.post(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        self._installation_tokens[installation_id] = {
            'token': data['token'],
            'expires_at': time.time() + 3600
        }

        return data['token']

    def get_client(self, installation_id: int) -> Github:
        token = self._get_installation_token(installation_id)
        auth = Auth.Token(token)
        return Github(auth=auth)

    def get_integration(self) -> GithubIntegration:
        auth = Auth.AppAuth(self.app_id, self.private_key)
        return GithubIntegration(auth=auth)

    def post_comment_reply(self, installation_id: int, repo_full_name: str,
                          pr_number: int, comment_id: int, body: str) -> Dict[str, Any]:
        client = self.get_client(installation_id)
        repo = client.get_repo(repo_full_name)
        pull = repo.get_pull(pr_number)

        comment = pull.create_review_comment_reply(comment_id, body)

        return {
            'id': comment.id,
            'html_url': comment.html_url,
            'created_at': comment.created_at.isoformat()
        }

    def get_file_content(self, installation_id: int, repo_full_name: str,
                        path: str, ref: str) -> str:
        client = self.get_client(installation_id)
        repo = client.get_repo(repo_full_name)

        try:
            content = repo.get_contents(path, ref=ref)
            if isinstance(content, list):
                return ""
            return content.decoded_content.decode('utf-8')
        except Exception:
            return ""

    def find_prs_by_author(self, installation_id: int, username: str,
                          state: str = 'open') -> list:
        client = self.get_client(installation_id)
        integration = self.get_integration()

        prs = []
        for installation in integration.get_installations():
            for repo in installation.get_repos():
                try:
                    pulls = repo.get_pulls(state=state)
                    for pr in pulls:
                        if pr.user and pr.user.login == username:
                            prs.append({
                                'repo': repo.full_name,
                                'number': pr.number,
                                'title': pr.title,
                                'html_url': pr.html_url
                            })
                except Exception:
                    continue

        return prs

