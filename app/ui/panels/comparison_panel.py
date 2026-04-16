from PyQt6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from app.models.comparison_models import ComparisonResult


class ComparisonPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("Comparison")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.output)

        self.setLayout(layout)

    def display_comparison(self, comparison_result: ComparisonResult):
        lines = []

        lines.append("=== Comparison Summary ===")
        lines.append(comparison_result.summary)
        lines.append("")

        lines.append("=== Field Comparison ===")
        lines.append("")
        for row in comparison_result.rows:
            lines.append(f"{row.field_name}")
            lines.append(f"  Left : {row.left_value}")
            lines.append(f"  Right: {row.right_value}")
            lines.append(f"  Changed: {'Yes' if row.changed else 'No'}")
            lines.append("")

        lines.append("=== Structured Request Diff ===")
        lines.append("")
        if comparison_result.request_structured_diffs:
            for item in comparison_result.request_structured_diffs:
                lines.append(f"- {item}")
        else:
            lines.append("No structured request differences detected.")
        lines.append("")

        lines.append("=== Structured Response Diff ===")
        lines.append("")
        if comparison_result.response_structured_diffs:
            for item in comparison_result.response_structured_diffs:
                lines.append(f"- {item}")
        else:
            lines.append("No structured response differences detected.")
        lines.append("")

        lines.append("=== Request Line Diff ===")
        lines.append("")
        lines.append(comparison_result.request_line_diff or "No line-level request diff.")
        lines.append("")

        lines.append("=== Response Line Diff ===")
        lines.append("")
        lines.append(comparison_result.response_line_diff or "No line-level response diff.")

        self.output.setPlainText("\n".join(lines))

    def clear(self):
        self.output.clear()