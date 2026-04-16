APP_NAME = "HuntPilot"
DEFAULT_LANGUAGE = "en"

WINDOW_MIN_WIDTH = 1650
WINDOW_MIN_HEIGHT = 900

PROJECTS_ROOT_DIR = "data/projects"

DEFAULT_SAMPLE_REQUEST = """PATCH /api/users/123?account_id=456 HTTP/1.1
Host: example.com
Authorization: Bearer token123
Cookie: sessionid=abc123; theme=dark
Content-Type: application/json

{"user_id":123,"role":"admin","email":"test@example.com","status":"active","plan":"pro"}"""

DEFAULT_SAMPLE_RESPONSE = """HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 97

{"error":"forbidden","message":"You are not allowed to modify this user","code":"AUTH_403"}"""