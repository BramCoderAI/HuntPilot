from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class HTTPRequest:
    raw_text: str
    method: str = ""
    url: str = ""
    scheme: str = ""
    host: str = ""
    port: Optional[int] = None
    path: str = ""
    query_params: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    content_type: str = ""
    body: str = ""
    body_json: Optional[Any] = None
    body_form: Dict[str, str] = field(default_factory=dict)


@dataclass
class HTTPResponse:
    raw_text: str
    status_code: int = 0
    reason_phrase: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    content_type: str = ""
    body: str = ""
    body_json: Optional[Any] = None
    body_length: int = 0


@dataclass
class HTTPExchange:
    request: HTTPRequest
    response: Optional[HTTPResponse] = None