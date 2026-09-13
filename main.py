#!/usr/bin/env python3
"""
main.py
=======

Command-line entry point for the GRC Audit Agent demo.

Usage:
    python main.py
    python main.py --policy meridian_change_management_policy.md --framework change_management_controls.json

Run with no arguments to audit the included Meridian Trust Bank sample
policy against the included change-management controls checklist.
"""

import argparse
import os
import sys

from dotenv import load_dotenv

# Make sure "from grc_agent import ..." works when running this file
# directly from the project root.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from grc_agent.agent import GRCAuditAgent  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Run the GRC audit gap-analysis agent.")
    parser.add_argument(
        "--policy",
        default="meridian_change_management_policy.md",
        help="Policy document filename (in data/) to audit.",
    )
    parser.add_argument(
        "--framework",
        default="change_management_controls.json",
        help="Controls framework filename (in data/) to audit against.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the turn-by-turn tool-call log and only print the final summary.",
    )
    args = parser.parse_args()

    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY is not set.\n"
            "Copy .env.example to .env and add your own key from "
            "https://console.anthropic.com/settings/keys"
        )
        sys.exit(1)

    task = (
        f"Please audit the policy document '{args.policy}' against the "
        f"controls framework '{args.framework}'. Produce a full gap "
        f"analysis report and save it."
    )

    agent = GRCAuditAgent(verbose=not args.quiet)
    print(f"Running audit: {args.policy}  vs.  {args.framework}")
    print("(This calls the Claude API and may take 20-60 seconds...)\n")

    summary, saved_report = agent.run(task)

    print("\n=== Agent's final summary ===\n")
    print(summary)

    if saved_report:
        print(f"\nReport saved to: reports/{saved_report}")
    else:
        print(
            "\nWARNING: the agent did not save a report this run. See the "
            "log above for what happened — it may have stopped early."
        )


if __name__ == "__main__":
    main()
