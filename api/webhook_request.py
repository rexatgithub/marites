from src.utils import setup_logger
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


logger = setup_logger()


class WebhookRequest(BaseHTTPRequestHandler):
    def response(self, code: int, message: str = None, error: str = None, should_log: bool = True, payload: dict = None):
        self.log(message, error, should_log)
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload or {'message': message}).encode())

    def log(self, message: str, error: str = None, should_log: bool = True):
        if not should_log:
            return

        if error is not None:
            logger.warning(f'{message}: {error}')
            return

        logger.info(message)
        return
