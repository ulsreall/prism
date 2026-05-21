"""
PRISM - Duplication Finder Agent
Estimated token consumption: ~20K tokens per analysis

Detects:
- Exact duplicate code blocks
- Similar (near-duplicate) code blocks
- DRY (Don't Repeat Yourself) violations
- Structural duplication patterns
- Cross-file duplication indicators
"""

import re
import hashlib
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict
from difflib import SequenceMatcher


class DuplicationFinderAgent:
    """Agent for detecting code duplication and DRY violations."""

    AGENT_NAME = "Duplication Finder"
    ESTIMATED_TOKENS = 20000

    # Minimum block size for duplication detection (in lines)
    MIN_BLOCK_SIZE = 4
    MIN_TOKEN_BLOCK_SIZE = 10

    async def analyze(self, code: str, context: dict) -> Dict[str, Any]:
        """Detect code duplication across multiple dimensions."""
        findings = []
        lines = code.split('\n')

        # 1. Exact line duplication
        exact_dupes = self._find_exact_duplicates(lines)
        findings.extend(exact_dupes)

        # 2. Block duplication (consecutive similar lines)
        block_dupes = self._find_block_duplicates(lines)
        findings.extend(block_dupes)

        # 3. Structural duplication (same structure, different names)
        structural_dupes = self._find_structural_duplicates(code, lines)
        findings.extend(structural_dupes)

        # 4. Similar functions
        similar_funcs = self._find_similar_functions(code)
        findings.extend(similar_funcs)

        # 5. DRY violations
        dry_violations = self._find_dry_violations(code, lines)
        findings.extend(dry_violations)

        # 6. Copy-paste patterns
        copy_paste = self._find_copy_paste_patterns(code, lines)
        findings.extend(copy_paste)

        # Calculate metrics
        total_lines = len(lines)
        duplicated_lines = self._count_duplicated_lines(lines)
        duplication_ratio = duplicated_lines / max(1, total_lines) * 100

        score = self._calculate_score(duplication_ratio, len(findings), total_lines)

        metrics = {
            "score": score,
            "total_lines": total_lines,
            "duplicated_lines": duplicated_lines,
            "duplication_ratio": round(duplication_ratio, 1),
            "exact_duplicates": len(exact_dupes),
            "block_duplicates": len(block_dupes),
            "structural_duplicates": len(structural_dupes),
            "similar_functions": len(similar_funcs),
            "dry_violations": len(dry_violations),
            "copy_paste_patterns": len(copy_paste),
            "total_duplicate_groups": len(exact_dupes) + len(block_dupes) + len(structural_dupes),
            "estimated_reducible_lines": int(duplicated_lines * 0.6)
        }

        tokens_used = len(code) // 3 + len(findings) * 200 + 800  # Duplicates are token-heavy
        return {"findings": findings, "metrics": metrics, "tokens_used": tokens_used}

    def _find_exact_duplicates(self, lines: List[str]) -> List[Dict]:
        """Find exact duplicate lines (ignoring whitespace)."""
        findings = []
        line_hashes = defaultdict(list)

        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 15 and not stripped.startswith(('#', '//', '"""', "'''")):
                h = hashlib.md5(stripped.encode()).hexdigest()
                line_hashes[h].append(i + 1)

        # Find groups of duplicated lines
        seen_groups = set()
        for h, line_nums in line_hashes.items():
            if len(line_nums) >= 3:
                group_key = tuple(sorted(line_nums[:5]))
                if group_key not in seen_groups:
                    seen_groups.add(group_key)
                    findings.append({
                        "severity": "warning",
                        "category": "exact_duplicate",
                        "message": f"Line appears {len(line_nums)} times (lines: {', '.join(map(str, line_nums[:5]))}{'...' if len(line_nums) > 5 else ''})",
                        "line_start": line_nums[0],
                        "suggestion": "Extract this repeated code into a shared function or constant",
                        "confidence": 0.95
                    })

        return findings[:10]

    def _find_block_duplicates(self, lines: List[str]) -> List[Dict]:
        """Find duplicate blocks of consecutive lines."""
        findings = []
        blocks = {}

        # Normalize lines (strip whitespace, ignore comments)
        normalized = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                normalized.append((stripped, lines.index(line) + 1))
            else:
                normalized.append(('', -1))

        # Hash blocks of consecutive lines
        block_size = self.MIN_BLOCK_SIZE
        for i in range(len(normalized) - block_size + 1):
            block_lines = [normalized[j][0] for j in range(i, i + block_size)]
            if all(block_lines):
                block_text = '\n'.join(block_lines)
                block_hash = hashlib.md5(block_text.encode()).hexdigest()

                if block_hash in blocks:
                    original_start = blocks[block_hash]
                    current_start = i + 1
                    if abs(current_start - original_start) > block_size:
                        findings.append({
                            "severity": "error",
                            "category": "block_duplicate",
                            "message": f"Duplicate block of {block_size} lines at lines {original_start} and {current_start}",
                            "line_start": current_start,
                            "line_end": current_start + block_size - 1,
                            "suggestion": "Extract this block into a shared function",
                            "confidence": 0.9
                        })
                else:
                    blocks[block_hash] = i + 1

        return findings[:10]

    def _find_structural_duplicates(self, code: str, lines: List[str]) -> List[Dict]:
        """Find code blocks with same structure but different names/values."""
        findings = []

        # Extract function bodies and normalize them
        functions = []
        for match in re.finditer(r'(?:async\s+)?def\s+(\w+)\s*\([^)]*\)(.*?)(?=\ndef\s|\nclass\s|\Z)',
                                 code, re.DOTALL | re.MULTILINE):
            func_name = match.group(1)
            func_body = match.group(2)
            # Normalize: replace identifiers with placeholders
            normalized = self._normalize_code(func_body)
            functions.append({
                "name": func_name,
                "body": func_body,
                "normalized": normalized,
                "line": code[:match.start()].count('\n') + 1
            })

        # Compare normalized function bodies
        for i in range(len(functions)):
            for j in range(i + 1, len(functions)):
                similarity = SequenceMatcher(
                    None,
                    functions[i]["normalized"],
                    functions[j]["normalized"]
                ).ratio()

                if similarity > 0.8 and len(functions[i]["body"]) > 50:
                    findings.append({
                        "severity": "warning",
                        "category": "structural_duplicate",
                        "message": f"Functions '{functions[i]['name']}' and '{functions[j]['name']}' are {similarity:.0%} similar in structure",
                        "line_start": functions[i]["line"],
                        "suggestion": f"Consider merging these functions with parameters for the differences",
                        "confidence": similarity
                    })

        return findings[:8]

    def _find_similar_functions(self, code: str) -> List[Dict]:
        """Find functions that are very similar and could be merged."""
        findings = []

        # Extract all functions with their full signatures and bodies
        functions = []
        for match in re.finditer(r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)(.*?)(?=\ndef\s|\nclass\s|\Z)',
                                 code, re.DOTALL | re.MULTILINE):
            func_name = match.group(1)
            params = match.group(2)
            body = match.group(3)
            functions.append({
                "name": func_name,
                "params": params,
                "body": body,
                "line": code[:match.start()].count('\n') + 1
            })

        # Compare each pair
        for i in range(len(functions)):
            for j in range(i + 1, len(functions)):
                # Check if they have similar names (suggesting same purpose)
                name_i = functions[i]["name"].rstrip('_v2').rstrip('_new').rstrip('_old')
                name_j = functions[j]["name"].rstrip('_v2').rstrip('_new').rstrip('_old')

                if name_i == name_j or self._names_similar(functions[i]["name"], functions[j]["name"]):
                    # Compare bodies
                    body_sim = SequenceMatcher(
                        None,
                        functions[i]["body"].strip(),
                        functions[j]["body"].strip()
                    ).ratio()

                    if body_sim > 0.7:
                        findings.append({
                            "severity": "warning",
                            "category": "similar_function",
                            "message": f"Functions '{functions[i]['name']}' and '{functions[j]['name']}' are {body_sim:.0%} similar",
                            "line_start": functions[i]["line"],
                            "suggestion": "Consider merging into a single parameterized function",
                            "confidence": body_sim
                        })

        return findings[:5]

    def _find_dry_violations(self, code: str, lines: List[str]) -> List[Dict]:
        """Find DRY (Don't Repeat Yourself) violations."""
        findings = []

        # Find repeated expression patterns
        expressions = defaultdict(list)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 25 and not stripped.startswith(('#', '"""', "'")):
                # Normalize the expression
                normalized = re.sub(r'\b\w+\b', 'ID', stripped)
                if normalized.count('ID') > 3:
                    expressions[normalized].append(i + 1)

        for pattern, line_nums in expressions.items():
            if len(line_nums) >= 3:
                findings.append({
                    "severity": "warning",
                    "category": "dry_violation",
                    "message": f"DRY violation: similar expression pattern repeated {len(line_nums)} times",
                    "line_start": line_nums[0],
                    "suggestion": "Extract this pattern into a reusable function or constant",
                    "confidence": 0.8
                })

        return findings[:5]

    def _find_copy_paste_patterns(self, code: str, lines: List[str]) -> List[Dict]:
        """Detect copy-paste patterns (e.g., slightly modified copies)."""
        findings = []

        # Look for numbered variable patterns (var1, var2, var3)
        numbered_vars = re.findall(r'\b(\w+?)(\d+)\b', code)
        var_groups = defaultdict(list)
        for base, num in numbered_vars:
            if int(num) > 0 and base not in ('line', 'col', 'row', 'page', 'version'):
                var_groups[base].append(int(num))

        for base, nums in var_groups.items():
            if len(nums) >= 3 and max(nums) - min(nums) + 1 == len(nums):
                findings.append({
                    "severity": "warning",
                    "category": "copy_paste",
                    "message": f"Numbered variables '{base}1' through '{base}{max(nums)}' suggest copy-paste pattern",
                    "suggestion": f"Use a list/array instead of numbered variables '{base}1', '{base}2', etc.",
                    "confidence": 0.85
                })

        # Look for repeated try/except blocks
        try_blocks = re.findall(r'try:(.*?)(?=except|finally|$)', code, re.DOTALL)
        if len(try_blocks) > 3:
            similarities = []
            for i in range(len(try_blocks)):
                for j in range(i + 1, len(try_blocks)):
                    sim = SequenceMatcher(None, try_blocks[i].strip(), try_blocks[j].strip()).ratio()
                    if sim > 0.8:
                        similarities.append(sim)
            if len(similarities) > 2:
                findings.append({
                    "severity": "info",
                    "category": "copy_paste",
                    "message": f"Found {len(similarities)} similar try/except blocks",
                    "suggestion": "Consider a common error handling decorator or context manager",
                    "confidence": 0.75
                })

        return findings[:5]

    def _normalize_code(self, code: str) -> str:
        """Normalize code by replacing identifiers with placeholders."""
        # Replace string literals
        normalized = re.sub(r'"[^"]*"', '"STR"', code)
        normalized = re.sub(r"'[^']*'", "'STR'", normalized)
        # Replace numbers
        normalized = re.sub(r'\b\d+\b', 'NUM', normalized)
        # Replace identifiers (but keep keywords)
        keywords = {'if', 'else', 'elif', 'for', 'while', 'def', 'class', 'return',
                   'import', 'from', 'try', 'except', 'finally', 'with', 'as', 'raise',
                   'yield', 'pass', 'break', 'continue', 'and', 'or', 'not', 'in', 'is',
                   'True', 'False', 'None', 'self', 'async', 'await'}
        words = normalized.split()
        normalized_words = []
        for word in words:
            clean = re.sub(r'[^a-zA-Z_]', '', word)
            if clean and clean not in keywords and len(clean) > 1:
                normalized_words.append(word.replace(clean, 'ID'))
            else:
                normalized_words.append(word)
        return ' '.join(normalized_words)

    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two function names are semantically similar."""
        # Remove common suffixes/prefixes
        clean1 = re.sub(r'(_v\d+|_new|_old|_copy|_temp|_\d+)$', '', name1)
        clean2 = re.sub(r'(_v\d+|_new|_old|_copy|_temp|_\d+)$', '', name2)

        if clean1 == clean2:
            return True

        # Check Levenshtein-like similarity
        return SequenceMatcher(None, clean1, clean2).ratio() > 0.8

    def _count_duplicated_lines(self, lines: List[str]) -> int:
        """Count total lines involved in duplication."""
        line_counts = defaultdict(int)
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 15 and not stripped.startswith(('#', '//')):
                line_counts[stripped] += 1

        duplicated = 0
        for line, count in line_counts.items():
            if count > 1:
                duplicated += count
        return duplicated

    def _calculate_score(self, duplication_ratio: float, finding_count: int,
                        total_lines: int) -> float:
        """Calculate duplication score (0-100, higher is better)."""
        score = 100.0

        # Penalize based on duplication ratio
        if duplication_ratio > 20:
            score -= 40
        elif duplication_ratio > 10:
            score -= 25
        elif duplication_ratio > 5:
            score -= 15
        elif duplication_ratio > 2:
            score -= 5

        # Penalize based on finding count relative to file size
        if total_lines > 0:
            findings_per_100 = finding_count / total_lines * 100
            score -= min(20, findings_per_100 * 2)

        return max(0, min(100, round(score, 1)))
