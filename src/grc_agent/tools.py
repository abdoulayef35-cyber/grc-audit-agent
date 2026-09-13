"""
tools.py
========

This file defines the "tools" our agent is allowed to use.

Why tools? A plain chatbot can only talk. An *agent* can act: it decides
which function to call, we run that real Python function on its behalf,
and we hand the result back so it can decide what to do next. That
request -> act -> observe -> decide loop (built in agent.py) is what
makes this an "agent" instead of a chatbot.

Each tool has two parts:
1. A JSON-schema *description* (in TOOLS below) that we send to Claude so
   it knows the tool exists, what it does, and what arguments it takes.
2. A real Python function (below) that actually does the work when
   Claude asks to use it.

Everything here is deliberately scoped to a local ./data and ./reports
folder — the agent can only read/write inside this project, never your
whole filesystem.
"""

import json
import os

# Resolve paths relative to this file so it works no matter where you run
# python from.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")


def load_controls_framework(framework_file: str) -> str:
    """Load a controls checklist (JSON) from the data folder and return it
    as a formatted string the model can read."""
    path = os.path.join(DATA_DIR, framework_file)
    if not os.path.exists(path):
        available = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
        return f"ERROR: '{framework_file}' not found in data/. Available frameworks: {available}"
    with open(path, "r", encoding="utf-8") as f:
        framework = json.load(f)
    return json.dumps(framework, indent=2)


def read_policy_document(policy_file: str) -> str:
    """Read a policy document (markdown/text) from the data folder."""
    path = os.path.join(DATA_DIR, policy_file)
    if not os.path.exists(path):
        available = [f for f in os.listdir(DATA_DIR) if f.endswith((".md", ".txt"))]
        return f"ERROR: '{policy_file}' not found in data/. Available documents: {available}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_audit_report(filename: str, content: str) -> str:
    """Save the agent's finished gap-analysis report to the reports folder."""
    if not filename.endswith(".md"):
        filename += ".md"
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved report to reports/{filename} ({len(content)} characters)."


# ---------------------------------------------------------------------------
# Tool schemas: this is the "menu" of tools we hand to Claude. The
# descriptions matter a lot — this is how the model decides *when* and
# *how* to call each one, so be as clear as you'd be briefing a new hire.
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "load_controls_framework",
        "description": (
            "Load a controls checklist/framework (as JSON) that lists the controls "
            "an auditor should test for a given domain. Use this first to know what "
            "'good' looks like before reviewing a policy document."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "framework_file": {
                    "type": "string",
                    "description": "Filename of the framework JSON in the data folder, e.g. 'change_management_controls.json'.",
                }
            },
            "required": ["framework_file"],
        },
    },
    {
        "name": "read_policy_document",
        "description": (
            "Read the full text of a company policy document that needs to be audited "
            "against a controls framework."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_file": {
                    "type": "string",
                    "description": "Filename of the policy document in the data folder, e.g. 'meridian_change_management_policy.md'.",
                }
            },
            "required": ["policy_file"],
        },
    },
    {
        "name": "save_audit_report",
        "description": (
            "Save the finished gap-analysis report as a markdown file. Call this once, "
            "after you have fully compared the policy against every control in the framework."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Report filename, e.g. 'meridian_change_management_gap_analysis.md'.",
                },
                "content": {
                    "type": "string",
                    "description": "The full markdown content of the audit report.",
                },
            },
            "required": ["filename", "content"],
        },
    },
]

# Maps tool name -> the Python function that implements it, so the agent
# loop can dispatch calls generically without a big if/elif chain.
TOOL_FUNCTIONS = {
    "load_controls_framework": load_controls_framework,
    "read_policy_document": read_policy_document,
    "save_audit_report": save_audit_report,
}
