# User Guide: GRC Audit Agent

This guide covers everything you need to run the agent — both ways: from
the terminal (command line) and from your browser (Streamlit). If you're
looking for how the agent is built or why it counts as "agentic AI," see
[README.md](README.md) instead; this document is purely about *using* it.

## 1. One-time setup

You only need to do this once.

1. **Install Python 3.9+** if you don't already have it (check with
   `python --version` or `python3 --version` in a terminal).
2. **Get a Claude API key** at
   [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys).
   New accounts get free trial credits — a single audit run costs a small
   fraction of a cent.
3. **Open a terminal inside this project folder** (the one containing
   `main.py`). On Windows: right-click an empty spot inside the folder in
   File Explorer and choose "Open in Terminal" (or `cd` to the folder's
   path).
4. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
5. **Add your API key:**
   - Copy `.env.example` to a new file named exactly `.env` (not
     `.env.txt` — on Windows, turn on "File name extensions" in File
     Explorer's View tab to confirm the name is right).
   - Open `.env` in a text editor and replace the placeholder with your
     real key, so the line reads:
     ```
     ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
     ```
   - Save the file.

That's it — setup is done. Everything below can be repeated as many times
as you like.

## 2. Option A: Run it from the terminal

This is the fastest way to run an audit and see the raw output.

**Basic run** (uses the default sample policy and framework):
```
python main.py
```

**Choose which policy and framework to audit**, using files that live in
the `data/` folder:
```
python main.py --policy meridian_change_management_policy.md --framework nist_800_53_cm_controls.json
```

**Available flags:**

| Flag | What it does | Default |
|---|---|---|
| `--policy` | Policy document filename (must be in `data/`) | `meridian_change_management_policy.md` |
| `--framework` | Controls framework filename (must be in `data/`) | `change_management_controls.json` |
| `--quiet` | Hide the turn-by-turn tool-call log, show only the final summary | off |

**What you'll see:** a line confirming which files are being audited,
then — unless you passed `--quiet` — a live log of each step the agent
takes (loading the framework, reading the policy, saving the report),
then a plain-language summary, then either a line telling you where the
report was saved or a warning if the run didn't finish.

**Where results go:** open the `reports/` folder — you'll find a new
`.md` file with the full findings table and remediation plan. Open it
with any text editor, or with something that renders markdown (VS Code,
Typora, GitHub, etc.) for nicer formatting.

**On Windows, if `streamlit` or other commands say "not recognized"**
later on, prefix the command with `python -m`, e.g. `python -m streamlit
run app.py` instead of `streamlit run app.py` — this runs the tool
through Python directly instead of relying on it being on your system
PATH.

## 3. Option B: Run it in your browser (Streamlit)

This gives you a visual interface instead of a terminal window — better
for demos.

**Launch it:**
```
streamlit run app.py
```
(If that command isn't recognized, use `python -m streamlit run app.py`
instead.)

A browser tab should open automatically at `http://localhost:8501`. If it
doesn't, copy that URL from the terminal into your browser manually.

**Using the page:**

1. Click the **policy document** dropdown and choose the file you want to
   audit. Click "Preview policy document" below it to double-check you
   picked the right one.
2. Click the **controls framework** dropdown and choose which framework
   to audit against. Click "Preview framework" to confirm — it shows how
   many controls are in it.
3. Click **▶ Run Audit**.
4. Watch the status box — it shows each tool call live as the agent
   works, the same information as the terminal log, just in the browser.
5. When it finishes, the **Summary** and **Full Report** appear on the
   page, with a **Download report (.md)** button.

**Important:** the two dropdowns don't automatically match each other —
they each default independently to whichever filename sorts first
alphabetically. Always double-check both dropdowns show what you intend
before clicking Run Audit, especially if you've added your own files.

**To stop the app:** go back to the terminal window it's running in and
press `Ctrl+C`.

## 4. Testing your own policy or framework

You don't need to change any code to test a new document:

1. Save your policy as a `.md` or `.txt` file inside the `data/` folder.
2. Save any new controls framework as a `.json` file (matching the
   structure of the existing ones) inside `data/`.
3. It'll immediately show up as an option — in the CLI via `--policy`
   /`--framework`, and in the Streamlit dropdowns.

If you're using a real, publicly-published policy (rather than the
included fictional samples), keep it out of your public GitHub repo —
add its filename to `.gitignore` — since it's someone else's document,
even if it's publicly posted.

## 5. Troubleshooting

**"ANTHROPIC_API_KEY is not set"** — your `.env` file is missing, in the
wrong location, or named wrong (check for a hidden `.txt` extension). See
step 5 of setup above.

**A connection error / "server disconnected"** — usually a transient
network blip; the agent automatically retries a few times on its own. If
it fails every single time, check whether you're on a VPN — some VPNs
interfere with this kind of connection, and turning it off often fixes
it immediately.

**The report looks identical to a previous run**, or the app shows an
error that no report was saved — the agent stopped before finishing.
This is now handled automatically (it self-corrects and retries up to
twice), but if it still happens, just click **Run Audit** again (or
re-run `python main.py`).

**The dropdown/flags picked the wrong policy or framework** — this
almost always means only one of the two selections was actually changed.
Double-check both explicitly rather than assuming a default is what you
intended (see the note in section 3).

**Everything seems to run, but you have multiple copies of this project
folder on your machine** — pick one folder to be "the" project going
forward and stop copying files between copies; running from the wrong
folder (with stale files) is a common source of confusing results.
