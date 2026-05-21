#!/usr/bin/env python3
"""PRISM Web Dashboard — Code Quality Metrics Platform."""

from flask import Flask, render_template, request, jsonify
import random
import time
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

AGENTS = [
    {"name": "Complexity Analyzer", "desc": "Cyclomatic/cognitive complexity, nesting depth", "tokens": 16000, "status": "active", "runs": 4872, "success": 99.2, "avg_time": 3.4},
    {"name": "Maintainability Scorer", "desc": "Maintainability index, technical debt ratio", "tokens": 14000, "status": "active", "runs": 4650, "success": 99.5, "avg_time": 2.8},
    {"name": "Code Smell Detector", "desc": "God class, long method, feature envy, data clumps", "tokens": 18000, "status": "active", "runs": 4520, "success": 98.8, "avg_time": 4.1},
    {"name": "Naming Convention Checker", "desc": "Naming patterns, consistency, readability", "tokens": 12000, "status": "active", "runs": 4100, "success": 99.7, "avg_time": 2.1},
    {"name": "Duplication Finder", "desc": "Copy-paste detection, similar blocks, DRY violations", "tokens": 20000, "status": "active", "runs": 3890, "success": 98.5, "avg_time": 5.2},
    {"name": "Style Compliance", "desc": "PEP8/ESLint rules, formatting, line length", "tokens": 12000, "status": "active", "runs": 4200, "success": 99.9, "avg_time": 1.8},
    {"name": "Documentation Coverage", "desc": "Docstring coverage, comment density, API docs", "tokens": 14000, "status": "active", "runs": 3650, "success": 99.1, "avg_time": 3.0},
    {"name": "Test Coverage Analyzer", "desc": "Test patterns, assertion quality, edge cases", "tokens": 16000, "status": "active", "runs": 3400, "success": 98.9, "avg_time": 3.7},
    {"name": "Coupling Analyzer", "desc": "Afferent/efferent coupling, instability, abstractness", "tokens": 18000, "status": "active", "runs": 3150, "success": 99.3, "avg_time": 4.4},
    {"name": "Quality Gate", "desc": "Pass/fail scoring, thresholds, trend analysis", "tokens": 15000, "status": "active", "runs": 4700, "success": 99.6, "avg_time": 2.5},
]

ANALYSES = [
    {"id": "a1", "file": "src/auth/login.py", "score": 82, "time": "2 min ago", "findings": 12, "tokens": 143000},
    {"id": "a2", "file": "src/api/routes.py", "score": 71, "time": "5 min ago", "findings": 23, "tokens": 156000},
    {"id": "a3", "file": "src/models/user.py", "score": 91, "time": "8 min ago", "findings": 4, "tokens": 138000},
    {"id": "a4", "file": "src/utils/helpers.py", "score": 65, "time": "12 min ago", "findings": 31, "tokens": 162000},
    {"id": "a5", "file": "src/services/payment.py", "score": 88, "time": "15 min ago", "findings": 7, "tokens": 149000},
    {"id": "a6", "file": "src/db/connection.py", "score": 76, "time": "18 min ago", "findings": 18, "tokens": 151000},
]

FINDINGS = [
    {"severity": "critical", "title": "SQL injection vulnerability in query builder", "agent": "Code Smell Detector", "line": 42},
    {"severity": "critical", "title": "Cyclomatic complexity exceeds 25 in main()", "agent": "Complexity Analyzer", "line": 108},
    {"severity": "high", "title": "God class detected: UserManager (342 lines, 18 methods)", "agent": "Code Smell Detector", "line": 1},
    {"severity": "high", "title": "Duplicate code block (87% similarity) in utils.py", "agent": "Duplication Finder", "line": 55},
    {"severity": "medium", "title": "Missing docstring on public API: create_user()", "agent": "Documentation Coverage", "line": 23},
    {"severity": "medium", "title": "Inconsistent naming: camelCase mixed with snake_case", "agent": "Naming Checker", "line": 67},
    {"severity": "low", "title": "Line exceeds 120 characters (142 chars)", "agent": "Style Compliance", "line": 89},
    {"severity": "info", "title": "Consider extracting validation logic to separate module", "agent": "Coupling Analyzer", "line": 34},
]


@app.route("/")
def dashboard():
    total_tokens = sum(a["tokens"] * a["runs"] for a in AGENTS)
    return render_template("dashboard.html", agents=AGENTS, analyses=ANALYSES,
                           total_tokens=total_tokens, total_analyses=sum(a["runs"] for a in AGENTS))


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if request.method == "POST":
        code = request.form.get("code", "")
        filename = request.form.get("filename", "untitled.py")
        selected_agents = request.form.getlist("agents")

        analysis_id = str(uuid.uuid4())[:8]
        score = random.randint(55, 95)
        findings_count = random.randint(3, 35)
        tokens_used = random.randint(120000, 170000)

        result = {
            "id": analysis_id,
            "file": filename,
            "score": score,
            "findings": findings_count,
            "tokens": tokens_used,
            "time": "just now",
            "code": code,
            "agent_results": [],
        }

        for agent in AGENTS:
            if not selected_agents or agent["name"] in selected_agents:
                result["agent_results"].append({
                    "name": agent["name"],
                    "findings": random.randint(0, 8),
                    "tokens": agent["tokens"],
                    "score": random.randint(60, 100),
                })

        return render_template("results.html", result=result, findings=FINDINGS)

    return render_template("analyze.html", agents=AGENTS)


@app.route("/results/<analysis_id>")
def results(analysis_id):
    result = {
        "id": analysis_id,
        "file": "src/example.py",
        "score": random.randint(55, 95),
        "findings": random.randint(5, 30),
        "tokens": random.randint(120000, 170000),
        "time": "just now",
        "code": "# Example code\ndef hello():\n    print('world')",
        "agent_results": [{"name": a["name"], "findings": random.randint(0, 5), "tokens": a["tokens"], "score": random.randint(60, 100)} for a in AGENTS],
    }
    return render_template("results.html", result=result, findings=FINDINGS)


@app.route("/agents")
def agents():
    return render_template("agents.html", agents=AGENTS)


@app.route("/stats")
def stats():
    daily_tokens = [(f"2026-05-{d:02d}", random.randint(60_000_000, 78_000_000)) for d in range(1, 22)]
    hourly = [(f"{h:02d}:00", random.randint(1_500_000, 5_000_000)) for h in range(24)]
    return render_template("stats.html", agents=AGENTS, daily_tokens=daily_tokens, hourly=hourly)


@app.route("/api/stats")
def api_stats():
    return jsonify({
        "total_tokens": sum(a["tokens"] * a["runs"] for a in AGENTS),
        "total_analyses": sum(a["runs"] for a in AGENTS),
        "agents": [{"name": a["name"], "tokens": a["tokens"] * a["runs"]} for a in AGENTS],
    })


@app.route("/api/agents")
def api_agents():
    return jsonify(AGENTS)


if __name__ == "__main__":
    print("PRISM Web Dashboard starting on http://0.0.0.0:8081")
    app.run(host="0.0.0.0", port=8081, debug=False)
