from urllib.parse import parse_qsl, urlparse

from app.models.http_models import HTTPRequest, HTTPResponse
from app.utils.json_utils import try_parse_json
from app.utils.text_utils import parse_cookie_header


def parse_http_request(raw_text: str) -> HTTPRequest:
    lines = raw_text.splitlines()

    if not lines:
        return HTTPRequest(raw_text=raw_text)

    request_line = lines[0].strip()
    request_line_parts = request_line.split()

    method = request_line_parts[0] if len(request_line_parts) > 0 else ""
    raw_target = request_line_parts[1] if len(request_line_parts) > 1 else ""

    headers = {}
    body_lines = []
    in_body = False

    for line in lines[1:]:
        if not in_body:
            if line.strip() == "":
                in_body = True
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        else:
            body_lines.append(line)

    body = "\n".join(body_lines)

    host = headers.get("Host", "")
    if raw_target.startswith("http://") or raw_target.startswith("https://"):
        full_url = raw_target
    elif host:
        full_url = f"https://{host}{raw_target}"
    else:
        full_url = raw_target

    parsed_url = urlparse(full_url)

    query_params = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
    cookies = parse_cookie_header(headers.get("Cookie", ""))
    content_type = headers.get("Content-Type", "")

    body_json = None
    body_form = {}

    if body.strip():
        parsed_body_json = try_parse_json(body)
        if parsed_body_json is not None:
            body_json = parsed_body_json
        elif "application/x-www-form-urlencoded" in content_type.lower():
            body_form = dict(parse_qsl(body, keep_blank_values=True))

    port = parsed_url.port
    if port is None:
        if parsed_url.scheme == "https":
            port = 443
        elif parsed_url.scheme == "http":
            port = 80

    return HTTPRequest(
        raw_text=raw_text,
        method=method,
        url=full_url,
        scheme=parsed_url.scheme,
        host=parsed_url.hostname or host,
        port=port,
        path=parsed_url.path or raw_target,
        query_params=query_params,
        headers=headers,
        cookies=cookies,
        content_type=content_type,
        body=body,
        body_json=body_json,
        body_form=body_form,
    )


def parse_http_response(raw_text: str) -> HTTPResponse:
    lines = raw_text.splitlines()

    if not lines:
        return HTTPResponse(raw_text=raw_text)

    status_line = lines[0].strip()
    status_line_parts = status_line.split()

    status_code = 0
    reason_phrase = ""

    if len(status_line_parts) >= 2:
        try:
            status_code = int(status_line_parts[1])
        except ValueError:
            status_code = 0

    if len(status_line_parts) >= 3:
        reason_phrase = " ".join(status_line_parts[2:])

    headers = {}
    body_lines = []
    in_body = False

    for line in lines[1:]:
        if not in_body:
            if line.strip() == "":
                in_body = True
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        else:
            body_lines.append(line)

    body = "\n".join(body_lines)
    content_type = headers.get("Content-Type", "")
    body_json = try_parse_json(body) if body.strip() else None

    return HTTPResponse(
        raw_text=raw_text,
        status_code=status_code,
        reason_phrase=reason_phrase,
        headers=headers,
        content_type=content_type,
        body=body,
        body_json=body_json,
        body_length=len(body),
    )