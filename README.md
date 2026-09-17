# Presence Coach — Windows desktop prototype

Presence is a Windows desktop application for live professional-coaching practice.
It supports two experiences:

- **I am a Coachee** — Presence acts as the coach.
- **I am a Coach** — the user coaches a simulated professional coachee with hidden scenario context, then reviews the session.

Repository: https://github.com/agilecoach-ashutosh/executive-coach-app

**Status: runnable source prototype, not a verified Windows release.** Live cloud
sessions, model availability, microphone/speaker behaviour, transcription quality,
and generated coaching feedback still require real-world testing.

## Start on your Windows PC

1. Put the repository in a permanent folder such as `C:\PresenceCoach`.
2. Install **Python 3.12 (64-bit)** from https://www.python.org/downloads/windows/
   including the Python launcher. Python 3.12 can coexist with newer Python versions.
   Alternatively run `winget install -e --id Python.Python.3.12`.
3. Double-click **Setup.cmd**. It creates `.venv`, installs dependencies, and creates
   a desktop shortcut that launches the current Coach/Coachee + Review experience.
4. Open **Presence Coach** from the desktop or double-click **Start.cmd**.
5. Open **Settings** and enter a Gemini API key.
6. Choose microphone/speaker devices, enable session consent, then begin.

### Get a Gemini API key

1. Sign in to Google AI Studio: https://aistudio.google.com/
2. Open the Gemini API key page: https://aistudio.google.com/apikey
3. Create a key for an available project.
4. Copy the key and paste it into **Presence → Settings**.
5. Optionally choose **Remember key** to store it through Windows Credential Manager.

Do not place API keys in GitHub, screenshots, exported transcripts, or messages.
Google controls API availability, quotas, pricing, and model access.

The live conversation defaults to `gemini-3.1-flash-live-preview`. The settings also
allow another Live AUDIO model. A normal text-only model cannot replace the live
conversation transport. Post-session developmental reviews use a separate text call,
currently preferring `gemini-3.8-flash` with `gemini-2.5-flash` as a fallback.

## Mode 1 — I am a Coachee

Presence acts as an AI reflection partner informed by professional coaching practice.
`coaching.py` contains the editable behavioural instructions. The prompt emphasizes
client ownership, listening, concise reflections, one open question at a time, consent
before challenge/exercises, non-leading exploration, and client-generated learning
and action.

Presence is not a human, therapist, ICF-credentialed coach, or substitute for
qualified professional support.

## Mode 2 — I am a Coach

The user becomes the coach and Presence becomes a simulated workplace coachee.
`scenarios.py` contains professional scenarios across environments such as technology,
banking, consulting, startups, manufacturing, product, pharmaceuticals, education,
and financial services.

The coach sees only the presenting client brief. The simulated client receives hidden
context—tensions, assumptions, competing values, and background details—and is
instructed to reveal them gradually rather than dump the whole scenario at the start.
The simulated coachee may hesitate, disagree, say “I don’t know,” respond naturally
to leading questions, and finish with partial clarity.

This mode is for **practice and mentor-coaching discussion**. An AI simulated coachee
is not represented as a genuine client for an official credential submission.

## Post-session Coach Practice review

When a Coach Practice session ends, Presence opens a review screen with locally
computed session metrics and an optional AI-generated developmental review.

### Local metrics

The current review shows:

- Session duration
- Coach / Coachee speaking-share estimate based on transcript word count
- Coach turns
- Coachee turns
- Coach questions detected from transcript punctuation
- Coach turns containing multiple questions
- Average coach-turn length
- Longest coach turn
- Recorded interruption notes

The speaking-share value is **not measured audio time**. Question counts also depend
on provider transcription punctuation. These are descriptive practice metrics, not
ICF scoring criteria.

### ACC / PCC / MCC developmental review

Choose **ACC**, **PCC**, or **MCC**, then click **Generate coaching review**.
`reviewer.py` sends only the visible Coach/Coachee transcript, visible scenario brief,
and local metrics to a separate text-model review call. The reviewer does **not**
receive the hidden simulated-client persona.

The generated review covers:

- What the coach did well, with transcript evidence
- Establishes and Maintains Agreements
- Cultivates Trust and Safety
- Maintains Presence
- Listens Actively
- Evokes Awareness
- Facilitates Client Growth
- Observable patterns to watch
- Three high-leverage practice edges
- Specific moments worth revisiting with alternative coaching moves
- A developmental bottom line

The review uses an ACC/PCC/MCC developmental lens informed by the **2025 ICF Core
Competencies** and the updated **Minimum Skills Requirements effective in 2026**.
It deliberately does **not** issue an official ICF score, pass/fail result, or claim
credential readiness. AI feedback should be checked with a qualified mentor coach or
other appropriately qualified human reviewer.

A **Review** button remains available in the top bar after a Coach Practice session so
the review window can be reopened. Reviews and transcripts can be exported as text.

## Voice-reactive interface

The main experience uses a procedural amber orb with particles, filaments, halos, and
state-dependent movement. Microphone amplitude drives the orb while listening; local
playback amplitude drives it while the AI is speaking. **Gentle motion** reduces
animation. The optimized launcher reduces Canvas work so dialogs and controls remain
responsive.

## During a conversation

| Control | Behaviour |
| --- | --- |
| Silence setting | Waits this long after detected speech before submitting the spoken turn. |
| Take your time | Holds the current spoken turn through silence until **I'm ready**. |
| I'm ready | Finishes the current active spoken turn. |
| Interrupt | Stops local AI playback and gives the human the floor. |
| Mute | Stops new microphone input. |
| End | Disconnects the live session and preserves the transcript in memory. |
| Send | Sends typed input into the connected conversation. |
| Export transcript | Saves a timestamped UTF-8 text transcript. |

The prototype uses turn-based voice rather than full-duplex echo-cancelled interruption.
Quiet-time detection is based on local audio amplitude, not semantic understanding.
Background noise can therefore affect turn detection. Headphones are recommended.

## Privacy and keys

- Audio and typed live-conversation data are processed by Google Gemini when using the current provider.
- Post-session AI review sends the visible transcript and descriptive metrics to Gemini only when the user explicitly requests a review.
- Conversations remain in application memory unless exported.
- Exported transcript/review files are ordinary unencrypted text files.
- The app does not currently store raw audio recordings on disk.
- No webcam, screen capture, computer-control agent, wake-word listener, or automatic transcript upload is included.
- Saved API keys use the OS keyring (Windows Credential Manager on Windows).
- **Forget saved key** removes the saved credential entry when available.

Starting a new session resets model context. There is no guaranteed hidden
cross-session memory or automatic session resumption. A crash can lose text that has
not been exported.

## Current source structure

```text
app.py              Base Tkinter UI and Gemini session controls
launch.py           Performance-optimized orb/dialog layer
practice_mode.py    Coach/Coachee role selection and AI coachee mode
practice_review.py  Post-session metrics/review UI and current application entry point
coaching.py         Presence-as-coach behavioural instructions and Transcript model
scenarios.py        Simulated professional coachee scenarios and hidden persona prompts
reviewer.py         Local metrics + ACC/PCC/MCC developmental review prompt/call
engine.py           Gemini Live audio transport and turn handling
```

`Start.cmd`, the Setup desktop shortcut, and the Windows packaging workflow now use
`practice_review.py` as the application entry point.

## Updating an existing source installation

The safest update path is:

```powershell
git pull
```

Then fully close any running Presence process and reopen it with **Start.cmd**.
If dependencies change in a future update, rerun **Setup.cmd**.

## Create a Windows installer

Open **Actions → Build Windows installer → Run workflow**. The workflow installs
Python dependencies, runs the automated tests, packages `practice_review.py` with
PyInstaller, and builds an Inno Setup installer artifact.

For a local build with Python 3.12 and Inno Setup 6 installed:

```powershell
py -3.12 -m pip install -r requirements.txt pyinstaller
py -3.12 -m PyInstaller --noconfirm --windowed --name PresenceCoach --collect-all sounddevice --collect-all google.genai --hidden-import keyring.backends.Windows practice_review.py
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" installer.iss
```

The resulting executable is unsigned unless you separately configure code signing.

## Verification

Run:

```powershell
python -m unittest discover -s tests -v
```

Automated tests cover coaching turn policy, transport behaviours, transcript handling,
and Coach Practice review metrics. Hardware mocks are used for transport tests; these
are not end-to-end live voice tests and do not establish coaching quality.

Before calling this a release, test on a clean Windows 11 installation at common
Windows display scales, with real microphones/speakers, live Gemini quotas, network
failure, English/Hindi/Hinglish sessions, long pauses, interruption, transcript export,
Coach Practice scenarios, and ACC/PCC/MCC review generation.

## ICF-related design references

Presence uses ICF material as a developmental reference, not as an endorsement or
claim of assessment authority.

- 2025 ICF Core Competencies: https://coachingfederation.org/resource/icf-core-competencies/
- ACC Minimum Skills Requirements: https://coachingfederation.org/resource/acc-minimum-skills-requirements/
- PCC Minimum Skills Requirements: https://coachingfederation.org/resource/pcc-minimum-skills-requirements/
- MCC Minimum Skills Requirements: https://coachingfederation.org/resource/mcc-minimum-skills-requirements/
- Gemini Live API: https://ai.google.dev/gemini-api/docs/live-api

See `reference/ICF-PRACTICE-DESIGN.md`, `COACHING-REVIEW.md`, and
`reference/AGILE-ORBIT-INTEGRATION.md` for the product's coaching-design notes and
manual review material.
