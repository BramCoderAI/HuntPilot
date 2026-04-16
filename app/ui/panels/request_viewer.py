from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

from app.models.http_models import HTTPRequest, HTTPResponse
from app.utils.json_utils import pretty_json


class RequestViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("Parsed Exchange")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.output)

        self.setLayout(layout)

    def display_exchange(self, request: HTTPRequest, response: HTTPResponse | None = None):
        lines = []

        lines.append("=== Parsed Request ===")
        lines.append(f"Method: {request.method or 'None'}")
        lines.append(f"URL: {request.url or 'None'}")
        lines.append(f"Scheme: {request.scheme or 'None'}")
        lines.append(f"Host: {request.host or 'None'}")
        lines.append(f"Port: {request.port if request.port is not None else 'None'}")
        lines.append(f"Path: {request.path or 'None'}")
        lines.append("")

        lines.append("Request Query Parameters:")
        if request.query_params:
            for key, value in request.query_params.items():
                lines.append(f"  {key}: {value}")
        else:
            lines.append("  None")
        lines.append("")

        lines.append("Request Headers:")
        if request.headers:
            for key, value in request.headers.items():
                lines.append(f"  {key}: {value}")
        else:
            lines.append("  None")
        lines.append("")

        lines.append("Request Cookies:")
        if request.cookies:
            for key, value in request.cookies.items():
                lines.append(f"  {key}: {value}")
        else:
            lines.append("  None")
        lines.append("")

        lines.append(f"Request Content-Type: {request.content_type or 'None'}")
        lines.append("")

        if request.body_json is not None:
            lines.append("Request JSON Body:")
            lines.append(pretty_json(request.body_json))
        elif request.body_form:
            lines.append("Request Form Body:")
            for key, value in request.body_form.items():
                lines.append(f"  {key}: {value}")
        elif request.body:
            lines.append("Request Raw Body:")
            lines.append(request.body)
        else:
            lines.append("Request Body: None")

        lines.append("")

        lines.append("=== Parsed Response ===")
        if response is None:
            lines.append("No response provided.")
        else:
            lines.append(f"Status Code: {response.status_code or 'None'}")
            lines.append(f"Reason Phrase: {response.reason_phrase or 'None'}")
            lines.append(f"Content-Type: {response.content_type or 'None'}")
            lines.append(f"Body Length: {response.body_length}")
            lines.append("")

            lines.append("Response Headers:")
            if response.headers:
                for key, value in response.headers.items():
                    lines.append(f"  {key}: {value}")
            else:
                lines.append("  None")
            lines.append("")

            if response.body_json is not None:
                lines.append("Response JSON Body:")
                lines.append(pretty_json(response.body_json))
            elif response.body:
                lines.append("Response Raw Body:")
                lines.append(response.body)
            else:
                lines.append("Response Body: None")

        self.output.setPlainText("\n".join(lines))

    def clear(self):
        self.output.clear()