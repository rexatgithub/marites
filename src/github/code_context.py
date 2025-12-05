from typing import Dict, Any, List


class CodeContextExtractor:
    def __init__(self, context_lines: int = 5):
        self.context_lines = context_lines

    def extract_from_diff(self, diff_hunk: str, commented_line: int) -> Dict[str, Any]:
        if not diff_hunk:
            return {
                'code': '',
                'start_line': 0,
                'end_line': 0,
                'highlighted_line': commented_line
            }

        lines = diff_hunk.split('\n')
        code_lines = []
        line_numbers = []
        current_line = None

        for line in lines:
            if line.startswith('@@'):
                parts = line.split('+')[1].split('@@')[0].strip()
                current_line = int(parts.split(',')[0]) if ',' in parts else int(parts)
                continue

            if current_line is not None:
                code_lines.append(line)
                line_numbers.append(current_line)
                if not line.startswith('-'):
                    current_line += 1

        return {
            'code': '\n'.join(code_lines),
            'start_line': line_numbers[0] if line_numbers else 0,
            'end_line': line_numbers[-1] if line_numbers else 0,
            'highlighted_line': commented_line
        }

    def extract_from_file(self, file_content: str, line_number: int) -> Dict[str, Any]:
        if not file_content:
            return {
                'code': '',
                'start_line': 0,
                'end_line': 0,
                'highlighted_line': line_number
            }

        lines = file_content.split('\n')
        total_lines = len(lines)

        start = max(0, line_number - self.context_lines - 1)
        end = min(total_lines, line_number + self.context_lines)

        context_lines = lines[start:end]

        return {
            'code': '\n'.join(context_lines),
            'start_line': start + 1,
            'end_line': end,
            'highlighted_line': line_number
        }

    def format_for_slack(self, context: Dict[str, Any], file_path: str) -> str:
        code = context['code']
        start = context['start_line']
        highlighted = context['highlighted_line']

        if not code:
            return f"_{file_path}_\n```\n(Code context unavailable)\n```"

        lines = code.split('\n')
        formatted_lines = []

        for i, line in enumerate(lines):
            current_line = start + i
            prefix = '→ ' if current_line == highlighted else '  '
            formatted_lines.append(f"{prefix}{current_line:4d} | {line}")

        return f"_{file_path}_\n```\n" + '\n'.join(formatted_lines) + "\n```"

