from http.server import BaseHTTPRequestHandler
import json
import os


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            checks = {
                'github_configured': bool(os.environ.get('GITHUB_APP_ID')),
                'slack_configured': bool(os.environ.get('SLACK_BOT_TOKEN')),
                'storage_configured': bool(os.environ.get('KV_REST_API_URL')),
            }

            env_vars = {
                'GITHUB_APP_ID': bool(os.environ.get('GITHUB_APP_ID')),
                'GITHUB_PRIVATE_KEY': bool(os.environ.get('GITHUB_PRIVATE_KEY')),
                'GITHUB_WEBHOOK_SECRET': bool(os.environ.get('GITHUB_WEBHOOK_SECRET')),
                'GITHUB_USERNAME': bool(os.environ.get('GITHUB_USERNAME')),
                'SLACK_BOT_TOKEN': bool(os.environ.get('SLACK_BOT_TOKEN')),
                'SLACK_SIGNING_SECRET': bool(os.environ.get('SLACK_SIGNING_SECRET')),
                'SLACK_USER_ID': bool(os.environ.get('SLACK_USER_ID')),
                'APP_SECRET_KEY': bool(os.environ.get('APP_SECRET_KEY')),
                'KV_REST_API_URL': bool(os.environ.get('KV_REST_API_URL')),
                'KV_REST_API_TOKEN': bool(os.environ.get('KV_REST_API_TOKEN')),
            }

            all_healthy = all(checks.values())

            response = {
                'status': 'healthy' if all_healthy else 'degraded',
                'checks': checks,
                'env_vars': env_vars,
                'missing': [k for k, v in env_vars.items() if not v]
            }

            self.send_response(200 if all_healthy else 503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            return

        except Exception as e:
            import traceback
            error_response = {
                'status': 'error',
                'error': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }

            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
            return

