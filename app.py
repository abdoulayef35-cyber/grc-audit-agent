"""
app.py
======

A visual, browser-based demo of the same agent that main.py runs from the
command line. It uses Streamlit, a Python library that turns a plain
script into a small web app — no HTML/CSS/JS needed.

Run it with:
    streamlit run app.py

This file doesn't add any new agent behavior; it's the exact same
GRCAuditAgent from src/grc_agent/agent.py, just with a nicer front end:
you pick a policy + framework from a dropdown, watch the agent's tool
calls happen live, and get the finished report rendered in the browser
with a download button.
"""

import json
import os
import sys

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from grc_agent.agent import GRCAuditAgent  # noqa: E402
from grc_agent.tools import DATA_DIR, REPORTS_DIR  # noqa: E402

load_dotenv()

st.set_page_config(page_title="GRC Audit Agent", page_icon="\U0001F6E1️", layout="wide")

st.title("\U0001F6E1️ GRC Audit Agent")
st.caption(
    "An AI agent that reads a policy document, compares it control-by-control "
    "against a framework, and writes a gap-analysis report — live, in your browser."
)

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.error(
        "ANTHROPIC_API_KEY is not set. Copy .env.example to .env, add your key "
        "from console.anthropic.com/settings/keys, and restart this app."
    )
    st.stop()

policy_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith((".md", ".txt")))
framework_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".json"))

col1, col2 = st.columns(2)

with col1:
    policy_file = st.selectbox("Policy document to audit", policy_files)
    with open(os.path.join(DATA_DIR, policy_file), encoding="utf-8") as f:
        policy_text = f.read()
    with st.expander("Preview policy document"):
        st.markdown(policy_text)

with col2:
    framework_file = st.selectbox("Controls framework to audit against", framework_files)
    with open(os.path.join(DATA_DIR, framework_file), encoding="utf-8") as f:
        framework_data = json.load(f)
    with st.expander(f"Preview framework ({len(framework_data.get('controls', []))} controls)"):
        st.json(framework_data)

st.divider()

run_clicked = st.button("▶ Run Audit", type="primary")

if run_clicked:
    status = st.status("Agent is working...", expanded=True)

    def log_callback(message: str):
        # Every log line the agent emits gets written straight into the
        # status box, so you see each tool call the moment it happens.
        status.write(message)

    agent = GRCAuditAgent(log_callback=log_callback)
    task = (
        f"Please audit the policy document '{policy_file}' against the "
        f"controls framework '{framework_file}'. Produce a full gap "
        f"analysis report and save it."
    )

    summary, saved_report = agent.run(task)
    status.update(label="Audit complete", state="complete", expanded=False)

    st.subheader("Summary")
    # unsafe_allow_html=True: Claude sometimes uses <br> tags inside markdown
    # table cells (a common trick to force a line break within a cell, since
    # plain markdown tables can't do that). Without this, Streamlit shows
    # the literal "<br>" text instead of rendering it as a line break. This
    # is safe here because the content is our own agent's output, not
    # arbitrary user/web input.
    st.markdown(summary, unsafe_allow_html=True)

    # agent.run() tells us exactly which filename (if any) it actually
    # saved during THIS run — we don't guess by grabbing whatever .md file
    # in reports/ happens to have the newest timestamp. That guess-based
    # approach used to silently show a stale report left over from a
    # previous run whenever the agent stopped early without saving a new
    # one, which was confusing (looked like a fresh result but wasn't).
    if saved_report:
        report_path = os.path.join(REPORTS_DIR, saved_report)
        with open(report_path, encoding="utf-8") as f:
            report_content = f.read()

        st.subheader("Full Report")
        st.markdown(report_content, unsafe_allow_html=True)
        st.download_button(
            "Download report (.md)",
            data=report_content,
            file_name=saved_report,
            mime="text/markdown",
        )
    else:
        st.error(
            "The agent did not save a report this run — it stopped early "
            "(see the log above for what it said). This is NOT the same as "
            "an old report from a previous run; nothing new was produced. "
            "Try clicking Run Audit again."
        )
