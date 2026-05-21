"""
PRISM - Complexity Analyzer Agent
Estimated token consumption: ~16K tokens per analysis

Analyzes:
- Cyclomatic complexity (McCabe)
- Cognitive complexity (SonarQube-style)
- Nesting depth analysis
- Function/method complexity scoring
- Class complexity metrics
"""

import re
import math
from typing import Dict, List, Any


class ComplexityAnalyzerAgent:
    """Agent for analyzing code complexity metrics."""

    AGENT_NAME = "Complexity Analyzer"
    ESTIMATED_TOKENS = 16000

    # Keywords that increase cyclomatic complexity
    DECISION_KEYWORDS = {
        'python': [r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b', r'\band\b',
                   r'\bor\b', r'\bexcept\b', r'\bwith\b', r'\bassert\b',
                   r'\bif\s+.*\belse\b', r'\b.*\bif\b.*\belse\b'],
        'javascript': [r'\bif\b', r'\belse\s+if\b', r'\bfor\b', r'\bwhile\b',
                       r'\b&&\b', r'\b\|\|\b', r'\bcatch\b', r'\bcase\b',
                       r'\b\?\b', r'\bdo\b'],
        'java': [r'\bif\b', r'\belse\s+if\b', r'\bfor\b', r'\bwhile\b',
                 r'\b&&\b', r'\b\|\|\b', r'\bcatch\b', r'\bcase\b',
                 r'\bdo\b', r'\b\?\b'],
    }

    # Cognitive complexity increment patterns
    COGNITIVE_NESTED = {
        'python': [r'\bif\b', r'\bfor\b', r'\bwhile\b'],
        'javascript': [r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\bswitch\b'],
        'java': [r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\bswitch\b'],
    }

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Analyze code complexity across multiple dimensions."""
        language = context.get("language", "python")
        findings = []
        metrics = {}
        tokens_used = 0

        lines = code.split('\n')
        lang_key = language.lower() if language.lower() in self.DECISION_KEYWORDS else 'python'

        # 1. Calculate cyclomatic complexity per function
        functions = self._extract_functions(code, lang_key)
        func_complexities = []

        for func in functions:
            cc = self._cyclomatic_complexity(func["body"], lang_key)
            func_complexities.append({
                "name": func["name"],
                "line": func["line"],
                "cyclomatic": cc,
                "cognitive": self._cognitive_complexity(func["body"], lang_key),
                "nesting_depth": self._max_nesting_depth(func["body"], lang_key),
                "loc": len(func["body"].split('\n'))
            })

            # Generate findings based on complexity
            if cc > 20:
                findings.append({
                    "severity": "critical",
                    "category": "complexity",
                    "message": f"Function '{func['name']}' has cyclomatic complexity {cc} (threshold: 10)",
                    "line_start": func["line"],
                    "line_end": func["line"] + len(func["body"].split('\n')),
                    "suggestion": f"Refactor '{func['name']}' by extracting sub-functions or reducing conditional branches",
                    "confidence": 0.95
                })
            elif cc > 10:
                findings.append({
                    "severity": "warning",
                    "category": "complexity",
                    "message": f"Function '{func['name']}' has high cyclomatic complexity {cc}",
                    "line_start": func["line"],
                    "suggestion": "Consider breaking this function into smaller, more focused functions",
                    "confidence": 0.9
                })

            # Cognitive complexity check
            cog = self._cognitive_complexity(func["body"], lang_key)
            if cog > 15:
                findings.append({
                    "severity": "warning",
                    "category": "cognitive_complexity",
                    "message": f"Function '{func['name']}' has cognitive complexity {cog} (threshold: 15)",
                    "line_start": func["line"],
                    "suggestion": "Reduce nesting and simplify control flow logic",
                    "confidence": 0.9
                })

            # Nesting depth check
            nesting = self._max_nesting_depth(func["body"], lang_key)
            if nesting > 4:
                findings.append({
                    "severity": "error",
                    "category": "nesting",
                    "message": f"Function '{func['name']}' has nesting depth {nesting} (max recommended: 4)",
                    "line_start": func["line"],
                    "suggestion": "Use early returns or extract nested logic into helper functions",
                    "confidence": 0.95
                })

        # 2. File-level complexity metrics
        total_cc = sum(fc["cyclomatic"] for fc in func_complexities)
        avg_cc = total_cc / len(func_complexities) if func_complexities else 0
        max_cc = max((fc["cyclomatic"] for fc in func_complexities), default=0)
        max_nesting = max((fc["nesting_depth"] for fc in func_complexities), default=0)
        avg_cognitive = (
            sum(fc["cognitive"] for fc in func_complexities) / len(func_complexities)
            if func_complexities else 0
        )

        # 3. Halstead metrics (simplified)
        halstead = self._halstead_metrics(code, lang_key)

        # 4. Calculate overall complexity score (0-100)
        score = self._calculate_score(avg_cc, max_cc, max_nesting, avg_cognitive)

        metrics = {
            "score": score,
            "cyclomatic_complexity": {
                "total": total_cc,
                "average": round(avg_cc, 2),
                "max": max_cc,
                "functions_over_threshold": sum(1 for fc in func_complexities if fc["cyclomatic"] > 10)
            },
            "cognitive_complexity": {
                "average": round(avg_cognitive, 2),
                "max": max((fc["cognitive"] for fc in func_complexities), default=0)
            },
            "nesting_depth": {
                "max": max_nesting,
                "average": round(
                    sum(fc["nesting_depth"] for fc in func_complexities) / len(func_complexities)
                    if func_complexities else 0, 2
                )
            },
            "halstead": halstead,
            "functions_analyzed": len(func_complexities),
            "function_details": func_complexities[:20]  # Top 20 for display
        }

        tokens_used = self._estimate_tokens(code, len(findings))
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _extract_functions(self, code: str, lang: str) -> List[Dict]:
        """Extract function definitions and their bodies."""
        functions = []
        lines = code.split('\n')

        if lang == 'python':
            pattern = re.compile(r'^(\s*)(async\s+)?def\s+(\w+)\s*\(')
            current_func = None
            func_indent = 0
            func_body_lines = []
            func_start = 0

            for i, line in enumerate(lines):
                match = pattern.match(line)
                if match:
                    if current_func:
                        functions.append({
                            "name": current_func,
                            "line": func_start,
                            "body": '\n'.join(func_body_lines)
                        })
                    current_func = match.group(3)
                    func_indent = len(match.group(1))
                    func_body_lines = [line]
                    func_start = i + 1
                elif current_func:
                    stripped = line.strip()
                    if stripped == '' or (len(line) - len(line.lstrip()) > func_indent):
                        func_body_lines.append(line)
                    elif stripped and not line[0].isspace() and len(line) - len(line.lstrip()) <= func_indent:
                        functions.append({
                            "name": current_func,
                            "line": func_start,
                            "body": '\n'.join(func_body_lines)
                        })
                        current_func = None
                        func_body_lines = []

            if current_func:
                functions.append({
                    "name": current_func,
                    "line": func_start,
                    "body": '\n'.join(func_body_lines)
                })
        else:
            # JavaScript/Java function detection
            pattern = re.compile(
                r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(|(\w+)\s*\([^)]*\)\s*\{|(\w+)\s*\([^)]*\)\s*\{)',
                re.MULTILINE
            )
            for match in pattern.finditer(code):
                name = match.group(1) or match.group(2) or match.group(3) or match.group(4) or "anonymous"
                line_num = code[:match.start()].count('\n') + 1
                # Extract body (simplified)
                body_start = match.end()
                brace_count = 1
                pos = body_start
                while pos < len(code) and brace_count > 0:
                    if code[pos] == '{':
                        brace_count += 1
                    elif code[pos] == '}':
                        brace_count -= 1
                    pos += 1
                body = code[match.start():pos]
                functions.append({"name": name, "line": line_num, "body": body})

        return functions

    def _cyclomatic_complexity(self, code: str, lang: str) -> int:
        """Calculate McCabe cyclomatic complexity."""
        cc = 1  # Base complexity
        patterns = self.DECISION_KEYWORDS.get(lang, self.DECISION_KEYWORDS['python'])

        for pattern in patterns:
            matches = re.findall(pattern, code)
            cc += len(matches)

        return cc

    def _cognitive_complexity(self, code: str, lang: str) -> int:
        """Calculate SonarQube-style cognitive complexity."""
        complexity = 0
        nesting_level = 0
        lines = code.split('\n')

        increment_patterns = self.COGNITIVE_NESTED.get(lang, self.COGNITIVE_NESTED['python'])

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue

            # Track nesting
            indent = len(line) - len(line.lstrip())
            base_indent = len(code.split('\n')[0]) - len(code.split('\n')[0].lstrip()) if code.split('\n')[0].strip() else 0
            current_nesting = max(0, (indent - base_indent) // 4)

            for pattern in increment_patterns:
                if re.search(pattern, line):
                    # Nesting increment
                    complexity += 1 + current_nesting

            # Boolean operators add complexity
            for bool_op in [r'\b(and|&&)\b', r'\b(or|\|\|)\b']:
                bool_matches = re.findall(bool_op, line)
                complexity += len(bool_matches)

        return complexity

    def _max_nesting_depth(self, code: str, lang: str) -> int:
        """Calculate maximum nesting depth."""
        lines = code.split('\n')
        if not lines:
            return 0

        # Use indentation-based nesting for Python
        if lang == 'python':
            max_depth = 0
            indent_stack = []
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                indent = len(line) - len(line.lstrip())
                while indent_stack and indent <= indent_stack[-1]:
                    indent_stack.pop()
                indent_stack.append(indent)
                # Depth is based on nesting of control structures
                control_words = re.findall(r'\b(if|elif|else|for|while|with|try|except|finally)\b', stripped)
                if control_words:
                    depth = len(indent_stack)
                    max_depth = max(max_depth, depth)
            return max_depth
        else:
            # Brace-based nesting for JS/Java
            max_depth = 0
            current_depth = 0
            for char in code:
                if char == '{':
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif char == '}':
                    current_depth = max(0, current_depth - 1)
            return max_depth

    def _halstead_metrics(self, code: str, lang: str) -> Dict:
        """Calculate simplified Halstead complexity metrics."""
        # Extract operators and operands
        operators = set()
        operands = set()
        total_operators = 0
        total_operands = 0

        # Common operators
        op_patterns = [
            r'[+\-*/=<>!&|^~%]+',
            r'\b(and|or|not|in|is|if|else|for|while|return|import|from|class|def)\b',
        ]

        for pattern in op_patterns:
            for match in re.finditer(pattern, code):
                operators.add(match.group())
                total_operators += 1

        # Operands (identifiers and literals)
        for match in re.finditer(r'\b[a-zA-Z_]\w*\b', code):
            word = match.group()
            if word not in {'and', 'or', 'not', 'in', 'is', 'if', 'else', 'for',
                           'while', 'return', 'import', 'from', 'class', 'def',
                           'async', 'await', 'try', 'except', 'finally', 'with',
                           'True', 'False', 'None', 'self'}:
                operands.add(word)
                total_operands += 1

        n1 = total_operators
        n2 = total_operands
        N1 = len(operators)
        N2 = len(operands)

        vocabulary = N1 + N2
        length = n1 + n2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (N1 / 2) * (n2 / N2) if N2 > 0 else 0
        effort = difficulty * volume

        return {
            "vocabulary": vocabulary,
            "length": length,
            "volume": round(volume, 2),
            "difficulty": round(difficulty, 2),
            "effort": round(effort, 2),
            "estimated_bugs": round(volume / 3000, 2)
        }

    def _calculate_score(self, avg_cc: float, max_cc: int, max_nesting: int,
                        avg_cognitive: float) -> float:
        """Calculate overall complexity score (0-100, higher is better)."""
        score = 100.0

        # Penalize high average cyclomatic complexity
        if avg_cc > 10:
            score -= min(30, (avg_cc - 10) * 3)
        elif avg_cc > 5:
            score -= (avg_cc - 5) * 2

        # Penalize extreme max cyclomatic complexity
        if max_cc > 20:
            score -= min(25, (max_cc - 20) * 2)
        elif max_cc > 10:
            score -= (max_cc - 10) * 1.5

        # Penalize deep nesting
        if max_nesting > 4:
            score -= min(20, (max_nesting - 4) * 5)

        # Penalize high cognitive complexity
        if avg_cognitive > 15:
            score -= min(25, (avg_cognitive - 15) * 2)

        return max(0, min(100, round(score, 1)))

    def _estimate_tokens(self, code: str, finding_count: int) -> int:
        """Estimate token consumption for this analysis."""
        # Rough estimate: 1 token per 4 chars of code + overhead per finding
        code_tokens = len(code) // 4
        finding_tokens = finding_count * 150
        base_overhead = 500
        return code_tokens + finding_tokens + base_overhead
