"""
agent.py
========

The core agent loop.

The pattern here is the same one used by real coding/ops agents (including
Claude Code itself), just shrunk down to something you can read start to
finish:

    1. Send Claude the conversation so far, plus the list of tools it's
       allowed to use.
    2. Claude replies with either:
         a) a final text answer -> we're done, or
         b) one or more "tool_use" requests -> Claude wants to call a
            function and see the result before continuing.
    3. If (b), we actually run that Python function, package the result
       as a "tool_result", append it to the conversation, and go back to
       step 1.

This keeps going until Claude stops asking for tools and gives a final
answer. That loop is the entire difference between a "chatbot" (one
question, one answer) and an "agent" (can take multiple actions toward a
goal before responding).
"""

import os
import time

import anthropic
from anthropic import Anthropic

from .tools import TOOLS, TOOL_FUNCTIONS

# Transient errors worth automatically retrying: dropped connections,
# timeouts, and "the server is temporarily overloaded" (529). A real
# network blip or a momentarily busy API is common and not a bug in this
# code, so we retry a few times with a short, increasing delay before
# giving up.
RETRYABLE_ERRORS = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.InternalServerError,
)

# You can override this with an environment variable if you want to try a
# different model. See https://docs.claude.com/en/docs/about-claude/models
# for the current list of available model names.
DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

SYSTEM_PROMPT = """\
You are an IT audit / GRC (Governance, Risk, and Compliance) assistant \
agent. You help a junior auditor perform gap analyses: comparing a \
company's written policy against a controls framework to identify which \
controls are fully met, partially met, or missing.

When asked to audit a policy against a framework:
1. Load the controls framework first, so you know exactly what to test for.
2. Read the policy document.
3. Go control-by-control. For each control, decide: Met, Partially Met, \
or Not Met, and cite the specific policy language (or lack thereof) that \
supports your call. Do not skip any control in the framework.
4. Write a clear, professional audit report in markdown with:
   - A one-paragraph executive summary (overall posture, count of \
     met/partial/not-met controls)
   - A findings table: Control ID | Title | Status | Evidence / Rationale
   - A "Recommended Remediation" section listing concrete next steps for \
     every control that is not fully met, ordered by risk (highest risk \
     first)
5. Save the report using the save_audit_report tool. Then give the user a \
short plain-language summary of what you found.

Be specific and evidence-based, the way a real IS auditor would be for a \
CISA-style walkthrough. Do not be vague ("policy could be improved") — \
name the exact gap.
"""


class GRCAuditAgent:
    """A small wrapper around the Claude API that runs the tool-use loop
    described above."""

    def __init__(self, model: str = DEFAULT_MODEL, verbose: bool = True, log_callback=None):
        # The Anthropic() client automatically reads ANTHROPIC_API_KEY from
        # your environment (we load it from .env in cli.py / app.py).
        self.client = Anthropic()
        self.model = model
        self.verbose = verbose
        # log_callback lets a UI (like the Streamlit app) receive each log
        # line and display it live, instead of the line only going to the
        # terminal via print(). If none is given, we fall back to print().
        self.log_callback = log_callback

    def _log(self, message: str):
        if self.log_callback is not None:
            self.log_callback(message)
        elif self.verbose:
            print(message)

    def _create_with_retry(self, messages, max_attempts: int = 4):
        """Call the API, automatically retrying transient failures (dropped
        connections, timeouts, momentary server overload) with a short
        backoff before giving up and re-raising the error."""
        delay_seconds = 2
        for attempt in range(1, max_attempts + 1):
            try:
                return self.client.messages.create(
                    model=self.model,
                    # A full gap-analysis report (findings table + remediation
                    # for every control) can run long. 4096 was too tight —
                    # it could cut the response off mid-tool-call, dropping
                    # the tail end of the JSON arguments entirely (that's
                    # what caused a missing 'content' argument in practice).
                    max_tokens=8192,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                )
            except RETRYABLE_ERRORS as error:
                if attempt == max_attempts:
                    raise
                self._log(
                    f"  (connection issue: {error.__class__.__name__} — "
                    f"retrying in {delay_seconds}s, attempt {attempt}/{max_attempts})"
                )
                time.sleep(delay_seconds)
                delay_seconds *= 2  # back off: 2s, 4s, 8s, ...

    def run(self, user_message: str, max_turns: int = 10, max_nudges: int = 2):
        """Run the agent loop until Claude gives a final text answer (or we
        hit max_turns as a safety limit against infinite loops).

        Returns an (summary_text, saved_report_filename) tuple.
        saved_report_filename is None if the agent never successfully
        called save_audit_report during this run — callers should treat
        that as "the audit did not actually finish" rather than assume a
        leftover report file from an earlier run is this run's output.
        """

        messages = [{"role": "user", "content": user_message}]
        saved_report_filename = None
        nudges_used = 0

        for turn in range(max_turns):
            self._log(f"\n--- Agent turn {turn + 1}: asking Claude what to do next ---")

            response = self._create_with_retry(messages)

            # Claude's reply becomes part of the conversation history,
            # whether it's a final answer or a request to use tools.
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "max_tokens":
                # The response got cut off mid-generation because it hit the
                # token limit. If this happened in the middle of a tool
                # call's JSON arguments, the tool_input below may be missing
                # fields entirely (this is exactly what caused a missing
                # 'content' argument to save_audit_report in practice) — the
                # try/except around the function call handles that safely,
                # but flag it here so it's visible in the log why.
                self._log(
                    "  (warning: response was cut off at the token limit — "
                    "a tool call's arguments may be incomplete as a result)"
                )

            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

            if tool_use_blocks:
                # Claude wants to call one or more tools before it
                # continues. We run each one and send the results back.
                tool_results = []
                for block in tool_use_blocks:
                    tool_name = block.name
                    tool_input = block.input
                    self._log(f"  -> Claude is calling tool: {tool_name}({tool_input})")

                    function = TOOL_FUNCTIONS.get(tool_name)
                    if function is None:
                        result = f"ERROR: no such tool '{tool_name}'"
                    else:
                        # Defensive: never let a malformed tool call (missing
                        # or bad arguments — e.g. a response cut off
                        # mid-JSON) crash the whole run. Turn it into an
                        # error the model can see and correct instead.
                        try:
                            result = function(**tool_input)
                        except TypeError as error:
                            result = (
                                f"ERROR: your call to '{tool_name}' was invalid — {error}. "
                                "Check that you provided every required argument "
                                "(filename AND content, for save_audit_report) and try again."
                            )
                        except Exception as error:  # noqa: BLE001 - last-resort safety net
                            result = f"ERROR: '{tool_name}' raised {error.__class__.__name__}: {error}"

                    if tool_name == "save_audit_report" and not str(result).startswith("ERROR"):
                        saved_report_filename = tool_input.get("filename")

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        }
                    )

                messages.append({"role": "user", "content": tool_results})
                continue

            # No tool calls in this response: Claude thinks it's done.
            final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )

            if saved_report_filename is not None:
                # A report was actually saved at some point in this run —
                # this is a legitimate completion.
                return final_text, saved_report_filename

            # Claude stopped without ever saving a report. This can happen
            # if it starts narrating ("Now I'll analyze...") and then ends
            # the turn without actually issuing the tool calls it described.
            # Rather than silently accepting an incomplete run (which would
            # leave a UI displaying a stale report from a previous run),
            # nudge Claude to actually finish, up to max_nudges times.
            if nudges_used >= max_nudges:
                self._log(
                    f"  (agent stopped without saving a report, after {max_nudges} "
                    "follow-up nudges — giving up)"
                )
                return final_text, None

            nudges_used += 1
            self._log(
                "  (agent stopped without saving a report — nudging it to finish, "
                f"attempt {nudges_used}/{max_nudges})"
            )
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "You have not finished yet — no report has been saved. "
                        "Continue: complete the control-by-control analysis for "
                        "every control in the framework, then call "
                        "save_audit_report to save the finished report."
                    ),
                }
            )

        return (
            "Stopped after reaching the maximum number of turns without "
            "saving a report. Try increasing max_turns or simplifying the request."
        ), saved_report_filename
