import re

def is_ngrok_url(url: str) -> bool:
    ngrok_pattern = r'^https?://[a-zA-Z0-9-]+\.ngrok-free\.app'
    return bool(re.match(ngrok_pattern, url))