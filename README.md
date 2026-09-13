# GRC Audit Agent

An AI agent that performs IT-audit gap analyses: it reads a company policy
document, compares it line-by-line against a controls framework, and
produces a professional audit finding report — the same core task a junior
IS auditor does by hand when testing change-management, access-control, or
similar controls.

Built as a portfolio project pairing hands-on AI agent development with an
IT-audit / GRC use case, using the included fictional "Meridian Trust Bank"
sample environment.

## What makes this an "agent" and not just a chatbot?

A chatbot answers one question and stops. This project gives Claude a set
of **tools** (real Python functions it can call) and runs a loop:

```
   ask Claude what to do  --->  Claude requests a tool call
          ^                              |
          |                              v
   feed the tool's result   <---   we run the real function
   back to Claude
```

Claude decides, on its own, to: load the controls framework, read the
policy document, work through each control, and save the finished report —
without being told the exact steps in code. That decision loop is what
"agentic AI" means in practice, and it's the same pattern used by tools
like Claude Code, just scoped down to one job.

See [`src/grc_agent/agent.py`](src/grc_agent/agent.py) for the ~80-line
loop itself, and [`src/grc_agent/tools.py`](src/grc_agent/tools.py) for the
three tools it's given.

## Project structure

```
grc-audit-agent/
├── main.py                    # CLI entry point
├── app.py                      # visual (browser) demo — same agent, Streamlit front end
├── src/grc_agent/
│   ├── agent.py                # the agent loop + system prompt
│   └── tools.py                # tool schemas + the functions behind them
├── data/
│   ├── change_management_controls.json      # sample controls framework (custom, 9 controls)
│   ├── nist_800_53_cm_controls.json          # real framework: NIST SP 800-53 Rev.5 CM family (7 controls)
│   └── meridian_change_management_policy.md # sample policy (has planted gaps)
└── reports/                   # generated gap-analysis reports land here
```

## Setup

1. **Get a Claude API key** at https://console.anthropic.com/settings/keys
   (new accounts get free trial credits — this demo costs well under a
   penny per run).
2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
3. **Add your key:**
   ```
   cp .env.example .env
   # then edit .env and paste in your key
   ```

## Run the demo

```
python main.py
```

This audits the included Meridian Trust Bank change-management policy
against the included 9-control framework and saves a report to
`reports/`. You'll see each tool call logged live as the agent works
through the framework — that's the agent loop from the diagram above,
happening in real time.

Run it against your own files by dropping a `.json` framework or
`.md`/`.txt` policy into `data/` and passing filenames:

```
python main.py --policy your_policy.md --framework your_framework.json
```

## Visual demo (browser)

For something more demoable than a terminal window, run the Streamlit
version instead:

```
streamlit run app.py
```

This opens a page in your browser where you pick the policy and
framework from dropdowns (with an expandable preview of each), click
**Run Audit**, and watch the agent's tool calls appear live in a status
box as it works — then the finished report renders right on the page,
with a button to download it. It's the exact same agent and system
prompt as `main.py`; only the front end is different.

## Two frameworks are included

- **`change_management_controls.json`** — a custom-written 9-control
  checklist, easy to read end-to-end.
- **`nist_800_53_cm_controls.json`** — the 7 controls from the real NIST
  SP 800-53 Revision 5 Configuration Management (CM) family that map to
  change management (CM-1, CM-2, CM-3, CM-4, CM-5, CM-6, CM-9). NIST
  publications are U.S. federal government works and are public domain.
  Control statements here are paraphrased/condensed for this demo — see
  NIST SP 800-53 Rev. 5 directly for the authoritative text. Auditing
  against this one is more credible to talk about in an interview
  ("mapped to NIST 800-53") than a self-written checklist.

Point either framework at either policy:
```
python main.py --policy your_policy.md --framework nist_800_53_cm_controls.json
```

## Testing against real-world policies

The sample Meridian Trust Bank policy is useful because you already know
the "right answer" (the gaps were planted on purpose). To really put the
agent through its paces, test it against a real, publicly published
policy — many universities post their IT change management policies
openly (a few examples: University of St. Thomas, Southern Illinois
University, University of Central Florida). Save the text as a `.md` or
`.txt` file in `data/` and it'll show up automatically in both `main.py`
and `app.py` — no code changes needed.

Two things worth knowing when you do this:
- **Formatting matters less than you'd think.** The agent just reads
  plain text, so a messy PDF-copy-paste works, though cleaning it into
  real markdown (`#`/`##` headings, no stray page numbers or line
  breaks mid-sentence) makes it easier for *you* to read while checking
  the agent's work.
- **Don't publish a real institution's full policy text in your public
  repo** — it's their document, not yours, even though it's publicly
  posted. Keep real downloaded policies out of git (add them to
  `.gitignore`) and, if you want to show this technique publicly, share
  the agent's generated report rather than the source document, or note
  generically that it was tested against "a publicly available
  university policy" without redistributing the whole thing.

## Why the sample policy has gaps on purpose

The included Meridian Trust Bank change-management policy is written to
realistically pass some controls and fail others (no segregation of
duties requirement, no mandatory risk assessment, no required rollback
plan, no change advisory board) so the agent's output can be checked
against a known-correct answer — the same way you'd validate any audit
tool before trusting it on a real engagement.

## Extending this project

Ideas for a v2, if you want to keep building:
- Add a second framework/domain (e.g. access-control or vendor-risk
  controls) and a matching sample policy.
- Add a `list_available_files` tool so the agent can discover documents
  itself instead of being told filenames.
- Let `app.py` accept an uploaded file instead of only picking from
  `data/`, so a reviewer can bring their own policy.
- Have the agent cross-reference findings against a live risk register
  (e.g. a CSV or small database) instead of just the policy text.

## Resume / portfolio framing

Something like:

> **GRC Audit Agent** — Built an autonomous AI agent (Python, Anthropic
> Claude API, tool-use/function-calling) that performs IT-audit gap
> analyses, comparing policy documents against a controls framework and
> generating structured findings reports; applied to a simulated bank
> change-management policy as a CISA-aligned portfolio exercise.
