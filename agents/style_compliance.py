"""
PRISM - Style Compliance Agent
Estimated token consumption: ~12K tokens per analysis

Analyzes:
- PEP8 compliance for Python
- Line length violations
- Whitespace issues
- Import ordering
- Indentation consistency
- Trailing whitespace
- Blank line conventions
"""

import re
from typing import Dict, List, Any
from collections import Counter


class StyleComplianceAgent:
    """Agent for checking code style compliance."""

    AGENT_NAME = "Style Compliance"
    ESTIMATED_TOKENS = 12000

    # PEP8 constants
    MAX_LINE_LENGTH = 79
    MAX_LINE_LENGTH_EXTENDED = 120
    INDENT_SIZE = 4

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Check code style compliance against language standards."""
        findings = []
        lines = code.split('\n')
        language = context.get("language", "python").lower()

        # 1. Line length violations
        length_findings = self._check_line_length(lines)
        findings.extend(length_findings)

        # 2. Trailing whitespace
        trailing_findings = self._check_trailing_whitespace(lines)
        findings.extend(trailing_findings)

        # 3. Indentation issues
        indent_findings = self._check_indentation(lines, language)
        findings.extend(indent_findings)

        # 4. Blank line conventions
        blank_findings = self._check_blank_lines(lines, language)
        findings.extend(blank_findings)

        # 5. Import style
        import_findings = self._check_import_style(code, lines, language)
        findings.extend(import_findings)

        # 6. Whitespace around operators
        ws_findings = self._check_operator_whitespace(code, lines)
        findings.extend(ws_findings)

        # 7. Comment style
        comment_findings = self._check_comment_style(lines, language)
        findings.extend(comment_findings)

        # 8. String quote consistency
        quote_findings = self._check_quote_consistency(code, language)
        findings.extend(quote_findings)

        # 9. Semicolons and unnecessary constructs
        syntax_findings = self._check_unnecessary_syntax(code, lines, language)
        findings.extend(syntax_findings)

        # Calculate metrics
        violation_types = Counter(f["category"] for f in findings)
        total_lines = len(lines)
        clean_lines = total_lines - len(set(f.get("line_start", 0) for f in findings if f.get("line_start")))

        score = self._calculate_score(findings, total_lines)

        metrics = {
            "score": score,
            "total_lines": total_lines,
            "total_violations": len(findings),
            "violations_per_100_lines": round(len(findings) / max(1, total_lines) * 100, 2),
            "violation_types": dict(violation_types),
            "clean_line_percentage": round(clean_lines / max(1, total_lines) * 100, 1),
            "max_line_length": max((len(line) for line in lines), default=0),
            "avg_line_length": round(sum(len(line) for line in lines) / max(1, total_lines), 1),
            "longest_line": max(lines, key=len, default="")[:80] if lines else ""
        }

        tokens_used = len(code) // 4 + len(findings) * 80 + 300
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _check_line_length(self, lines: List[str]) -> List[Dict]:
        """Check for lines exceeding maximum length."""
        findings = []
        violations_79 = 0
        violations_120 = 0

        for i, line in enumerate(lines):
            length = len(line.rstrip())
            if length > self.MAX_LINE_LENGTH_EXTENDED:
                violations_120 += 1
                if violations_120 <= 3:
                    findings.append({
                        "severity": "error",
                        "category": "line_length",
                        "message": f"Line {i+1} exceeds {self.MAX_LINE_LENGTH_EXTENDED} characters ({length} chars)",
                        "line_start": i + 1,
                        "suggestion": "Break long line using parentheses, backslash continuation, or refactoring",
                        "confidence": 0.95
                    })
            elif length > self.MAX_LINE_LENGTH:
                violations_79 += 1

        if violations_79 > 0:
            findings.append({
                "severity": "warning",
                "category": "line_length",
                "message": f"{violations_79} lines exceed {self.MAX_LINE_LENGTH} characters",
                "suggestion": f"Consider wrapping lines at {self.MAX_LINE_LENGTH} characters (PEP8)",
                "confidence": 0.9
            })

        return findings

    def _check_trailing_whitespace(self, lines: List[str]) -> List[Dict]:
        """Check for trailing whitespace."""
        findings = []
        violations = 0

        for i, line in enumerate(lines):
            if line != line.rstrip():
                violations += 1

        if violations > 0:
            findings.append({
                "severity": "warning",
                "category": "trailing_whitespace",
                "message": f"{violations} lines have trailing whitespace",
                "suggestion": "Remove trailing whitespace from all lines",
                "confidence": 0.95
            })

        return findings

    def _check_indentation(self, lines: List[str], language: str) -> List[Dict]:
        """Check indentation consistency."""
        findings = []

        if language == 'python':
            # Check for tabs
            tab_lines = [i+1 for i, line in enumerate(lines) if '\t' in line]
            if tab_lines:
                findings.append({
                    "severity": "error",
                    "category": "indentation",
                    "message": f"Found tabs in {len(tab_lines)} lines (Python should use spaces)",
                    "line_start": tab_lines[0],
                    "suggestion": "Use 4 spaces per indentation level (PEP8)",
                    "confidence": 0.95
                })

            # Check for inconsistent indent sizes
            indent_sizes = set()
            for line in lines:
                if line and line[0] == ' ':
                    indent = len(line) - len(line.lstrip())
                    if indent > 0:
                        # Find the indent step
                        for size in [2, 4, 8]:
                            if indent % size == 0:
                                indent_sizes.add(size)

            if len(indent_sizes) > 1 and 4 in indent_sizes:
                findings.append({
                    "severity": "info",
                    "category": "indentation",
                    "message": "Mixed indentation sizes detected",
                    "suggestion": "Use consistent 4-space indentation throughout",
                    "confidence": 0.7
                })

        return findings

    def _check_blank_lines(self, lines: List[str], language: str) -> List[Dict]:
        """Check blank line conventions."""
        findings = []

        if language == 'python':
            # Check for missing blank lines between top-level definitions
            prev_was_top_level = False
            blank_count = 0
            in_class = False

            for i, line in enumerate(lines):
                stripped = line.strip()

                if stripped == '':
                    blank_count += 1
                    continue

                if stripped.startswith('class '):
                    if prev_was_top_level and blank_count < 2:
                        findings.append({
                            "severity": "warning",
                            "category": "blank_lines",
                            "message": f"Expected 2 blank lines before class definition at line {i+1}",
                            "line_start": i + 1,
                            "suggestion": "Add 2 blank lines before top-level class/function definitions (PEP8)",
                            "confidence": 0.9
                        })
                    prev_was_top_level = True
                    in_class = True
                    blank_count = 0
                elif stripped.startswith('def ') and not line[0].isspace():
                    if prev_was_top_level and blank_count < 2:
                        findings.append({
                            "severity": "warning",
                            "category": "blank_lines",
                            "message": f"Expected 2 blank lines before function definition at line {i+1}",
                            "line_start": i + 1,
                            "suggestion": "Add 2 blank lines before top-level function definitions (PEP8)",
                            "confidence": 0.9
                        })
                    prev_was_top_level = True
                    blank_count = 0
                elif stripped.startswith('def ') and line[0].isspace():
                    if blank_count < 1 and in_class:
                        findings.append({
                            "severity": "info",
                            "category": "blank_lines",
                            "message": f"Expected 1 blank line before method definition at line {i+1}",
                            "line_start": i + 1,
                            "confidence": 0.8
                        })
                    blank_count = 0
                else:
                    blank_count = 0

            # Check for too many consecutive blank lines
            max_blanks = 0
            current_blanks = 0
            for line in lines:
                if line.strip() == '':
                    current_blanks += 1
                    max_blanks = max(max_blanks, current_blanks)
                else:
                    current_blanks = 0

            if max_blanks > 3:
                findings.append({
                    "severity": "info",
                    "category": "blank_lines",
                    "message": f"Found {max_blanks} consecutive blank lines",
                    "suggestion": "Use at most 2 consecutive blank lines",
                    "confidence": 0.85
                })

        return findings

    def _check_import_style(self, code: str, lines: List[str], language: str) -> List[Dict]:
        """Check import style and ordering."""
        findings = []

        if language == 'python':
            imports = []
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(('import ', 'from ')):
                    imports.append((i + 1, stripped))

            # Check for star imports
            for line_num, imp in imports:
                if 'import *' in imp:
                    findings.append({
                        "severity": "warning",
                        "category": "import_style",
                        "message": f"Star import at line {line_num}: '{imp}'",
                        "line_start": line_num,
                        "suggestion": "Import specific names instead of using star imports",
                        "confidence": 0.9
                    })

            # Check import ordering (stdlib, third-party, local)
            import_sections = []
            current_section = []
            for line_num, imp in imports:
                if imp.startswith('from .') or imp.startswith('import .'):
                    section = 'local'
                elif any(imp.startswith(f'from {m}') or imp.startswith(f'import {m}')
                        for m in ['os', 'sys', 're', 'json', 'math', 'datetime', 'time',
                                  'typing', 'collections', 'abc', 'io', 'pathlib', 'logging',
                                  'unittest', 'hashlib', 'copy', 'functools', 'itertools']):
                    section = 'stdlib'
                else:
                    section = 'third_party'
                import_sections.append((line_num, section))

            # Check if sections are mixed
            last_section = None
            for line_num, section in import_sections:
                if last_section and section != last_section:
                    # Check if we went backwards in the expected order
                    order = {'stdlib': 0, 'third_party': 1, 'local': 2}
                    if order.get(section, 2) < order.get(last_section, 2):
                        findings.append({
                            "severity": "info",
                            "category": "import_order",
                            "message": f"Import at line {line_num} may be out of order",
                            "line_start": line_num,
                            "suggestion": "Order imports: stdlib, then third-party, then local (PEP8)",
                            "confidence": 0.7
                        })
                        break
                last_section = section

        return findings

    def _check_operator_whitespace(self, code: str, lines: List[str]) -> List[Dict]:
        """Check whitespace around operators."""
        findings = []
        violations = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Check for missing spaces around = (except in keyword args)
            # This is simplified - real PEP8 checking is more complex
            if re.search(r'[^\s=!<>]=[^=\s]', stripped) and 'lambda' not in stripped:
                # Could be keyword arg, check context
                if not re.search(r'\w+\s*\([^)]*[^=!<>]=[^=\s]', stripped):
                    violations += 1

        if violations > 3:
            findings.append({
                "severity": "info",
                "category": "whitespace",
                "message": f"Found {violations} lines with inconsistent operator spacing",
                "suggestion": "Use single spaces around operators (PEP8)",
                "confidence": 0.7
            })

        return findings

    def _check_comment_style(self, lines: List[str], language: str) -> List[Dict]:
        """Check comment style conventions."""
        findings = []

        if language == 'python':
            inline_comments_no_space = 0
            for line in lines:
                stripped = line.strip()
                # Check for inline comments without proper spacing
                if '#' in stripped and not stripped.startswith('#'):
                    code_part, _, comment = stripped.partition('#')
                    if code_part and comment and not comment.startswith(' '):
                        inline_comments_no_space += 1

            if inline_comments_no_space > 0:
                findings.append({
                    "severity": "info",
                    "category": "comment_style",
                    "message": f"{inline_comments_no_space} inline comments missing space after #",
                    "suggestion": "Use '# comment' not '#comment' (PEP8)",
                    "confidence": 0.9
                })

        return findings

    def _check_quote_consistency(self, code: str, language: str) -> List[Dict]:
        """Check string quote style consistency."""
        findings = []

        if language == 'python':
            single_quotes = len(re.findall(r"(?<![\\])'[^']*'", code))
            double_quotes = len(re.findall(r'(?<![\\])"[^"]*"', code))
            total = single_quotes + double_quotes

            if total > 10:
                dominant = "single" if single_quotes > double_quotes else "double"
                minority = "double" if single_quotes > double_quotes else "single"
                minority_count = min(single_quotes, double_quotes)
                ratio = minority_count / total

                if ratio > 0.3:
                    findings.append({
                        "severity": "info",
                        "category": "quote_style",
                        "message": f"Mixed quote styles: {single_quotes} single, {double_quotes} double",
                        "suggestion": f"Consider using consistent {dominant} quotes throughout",
                        "confidence": 0.7
                    })

        return findings

    def _check_unnecessary_syntax(self, code: str, lines: List[str], language: str) -> List[Dict]:
        """Check for unnecessary syntax patterns."""
        findings = []

        if language == 'python':
            # Semicolons
            semicolons = sum(1 for line in lines if line.strip().endswith(';'))
            if semicolons > 0:
                findings.append({
                    "severity": "warning",
                    "category": "unnecessary_syntax",
                    "message": f"Found {semicolons} unnecessary semicolons",
                    "suggestion": "Remove semicolons - they are not needed in Python",
                    "confidence": 0.95
                })

            # Unnecessary parentheses in conditions
            unnecessary_parens = len(re.findall(r'if\s+\(([^)]+)\)\s*:', code))
            if unnecessary_parens > 2:
                findings.append({
                    "severity": "info",
                    "category": "unnecessary_syntax",
                    "message": f"Found {unnecessary_parens} unnecessary parentheses in if/while conditions",
                    "suggestion": "Remove unnecessary parentheses: 'if x:' not 'if (x):'",
                    "confidence": 0.85
                })

            # Comparison to None/True/False using == instead of is
            bad_comparisons = len(re.findall(r'[!=]=\s*(None|True|False)', code))
            if bad_comparisons > 0:
                findings.append({
                    "severity": "warning",
                    "category": "unnecessary_syntax",
                    "message": f"Found {bad_comparisons} comparisons to None/True/False using == instead of is",
                    "suggestion": "Use 'is None'/'is not None' instead of '== None'/'!= None'",
                    "confidence": 0.95
                })

        return findings

    def _calculate_score(self, findings: List[Dict], total_lines: int) -> float:
        """Calculate style compliance score (0-100)."""
        if total_lines == 0:
            return 100.0

        score = 100.0

        severity_penalties = {"critical": 8, "error": 4, "warning": 2, "info": 0.5}
        for finding in findings:
            score -= severity_penalties.get(finding["severity"], 1)

        # Normalize by file size
        violations_per_100 = len(findings) / total_lines * 100
        if violations_per_100 > 20:
            score -= 10
        elif violations_per_100 > 10:
            score -= 5

        return max(0, min(100, round(score, 1)))
