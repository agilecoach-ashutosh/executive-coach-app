# Presence Coach — Windows desktop prototype

Presence is a Windows desktop application for live professional-coaching practice.
It supports two experiences:

- **I am a Coachee** — Presence acts as the coach.
- **I am a Coach** — the user coaches a simulated professional coachee with hidden scenario context, then reviews the session.

Presence now supports two cloud AI providers:

- **Google Gemini** — native Gemini Live audio conversation.
- **Groq** — turn-based voice using Groq Whisper speech-to-text, a Groq-hosted LLM, and Groq Orpheus text-to-speech.

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
   a desktop shortcut.
4. Open **Presence Coach** from the desktop or double-click **Start.cmd**.
5. Open **Settings → AI provider** and choose **Google Gemini** or **Groq**.
6. Add the matching API key, choose microphone/speaker devices, enable session consent,
   then begin.

Do not place API keys in GitHub, screenshots, exported transcripts, or messages.
Provider availability, quotas, rate limits, and pricing are controlled by Google or Groq.

## Get a Google Gemini API key

1. Open Google AI Studio: https://aistudio.google.com/
2. Sign in with your Google account.
3. Open the API Keys page directly: https://aistudio.google.com/apikey
4. Choose **Create API key** and select/create a Google Cloud project if prompted.
5. Copy the generated key.
6. In Presence, open **Settings → AI provider → Google Gemini**.
7. Paste the key into **Gemini API key**.
8. Optionally enable **Remember key securely in Windows Credential Manager**.

The live Gemini conversation defaults to `gemini-3.1-flash-live-preview`. Model
availability is provider-controlled and may change.

## Get a Groq API key

1. Open GroqCloud Console: https://console.groq.com/
2. Sign in or create a Groq account.
3. Open the API Keys page directly: https://console.groq.com/keys
4. Click **Create API Key**.
5. Give the key a name such as **Presence Coach**.
6. Create the key and copy it immediately. Groq keys normally begin with `gsk_`.
7. In Presence, open **Settings → AI provider → Groq**.
8. Paste the key into **Groq API key**.
9. Optionally enable **Remember key securely in Windows Credential Manager**.

The default Groq pipeline is:

```text
Microphone
   ↓
whisper-large-v3-turbo
Speech → text
   ↓
openai/gpt-oss-120b
Coaching / simulated-coachee response
   ↓
canopylabs/orpheus-v1-english
Text → speech
   ↓
Speaker / headphones
```

Groq Whisper and the conversation model are multilingual. The current Groq Orpheus
voice model used by Presence is **English-only**, so Groq voice sessions instruct the
AI to speak its responses in English. Gemini remains the better option when spoken
Hindi/Hinglish output is important.

The Groq settings currently allow:

- Chat models: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `llama-3.3-70b-versatile`
- Speech recognition: `whisper-large-v3-turbo`, `whisper-large-v3`
- English Orpheus voices: `troy`, `austin`, `daniel`, `autumn`, `diana`, `hannah`

## In-app API-key help

Click the **ⓘ** button in the Presence top bar or **How to get a key ↗** in Settings.
The help window contains separate instructions and direct buttons for:

- **Gemini API Keys** → https://aistudio.google.com/apikey
- **Groq API Keys** → https://console.groq.com/keys

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
The reviewer receives only the visible Coach/Coachee transcript, visible scenario
brief, and local metrics. It does **not** receive the hidden simulated-client persona.

When Gemini is the selected provider, the review uses Gemini text generation. When
Groq is selected, the review uses the selected Groq chat model.

The review covers:

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
| End | Disconnects the session and preserves the transcript in memory. |
| Send | Sends typed input into the connected conversation. |
| Export transcript | Saves a timestamped UTF-8 text transcript. |

The prototype uses turn-based voice rather than full-duplex echo-cancelled interruption.
Quiet-time detection is based on local audio amplitude, not semantic understanding.
Background noise can therefore affect turn detection. Headphones are recommended.

## Privacy and keys

- With **Gemini**, live audio/text is processed by Google Gemini.
- With **Groq**, spoken turns are sent to Groq Whisper for transcription; conversation
  text is sent to the selected Groq chat model; AI response text is sent to Groq
  Orpheus for English speech generation.
- Post-session AI review sends the visible transcript and descriptive metrics only
  when the user explicitly requests a review, using the currently selected provider.
- Conversations remain in application memory unless exported.
- Exported transcript/review files are ordinary unencrypted text files.
- The app does not currently store raw session recordings on disk. Temporary WAV
  files used by the Groq turn pipeline are deleted after STT/TTS processing.
- No webcam, screen capture, computer-control agent, wake-word listener, or automatic
  transcript upload is included.
- Saved API keys use the OS keyring (Windows Credential Manager on Windows).
- **Forget saved key** removes the saved credential for the currently selected provider.

Starting a new session resets model context. There is no guaranteed hidden
cross-session memory or automatic session resumption. A crash can lose text that has
not been exported.

## Current source structure

```text
app.py              Base Tkinter UI and Gemini settings/session controls
engine.py           Gemini Live audio transport
launch.py           Performance-optimized orb/dialog layer
practice_mode.py    Coach/Coachee role selection and AI coachee mode
practice_review.py  Post-session metrics/review UI
provider_mode.py    Gemini/Groq provider selection and current application entry point
groq_engine.py      Groq Whisper → LLM → Orpheus turn-based voice engine
coaching.py         Presence-as-coach behavioural instructions and Transcript model
scenarios.py        Simulated professional coachee scenarios and hidden persona prompts
reviewer.py         Local metrics + ACC/PCC/MCC developmental review prompt
```

`Start.cmd`, the Setup desktop shortcut, and the Windows packaging workflow use
`provider_mode.py` as the application entry point.

## Updating an existing source installation

Run:

```powershell
git pull
```

Because Groq adds a new Python dependency, existing installations should then run:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Or rerun **Setup.cmd**. Then fully close Presence and reopen it with **Start.cmd**.

## Create a Windows installer

Open **Actions → Build Windows installer → Run workflow**. The workflow installs
Python dependencies, runs automated tests, packages `provider_mode.py` with PyInstaller,
and builds an Inno Setup installer artifact.

For a local build with Python 3.12 and Inno Setup 6 installed:

```powershell
py -3.12 -m pip install -r requirements.txt pyinstaller
py -3.12 -m PyInstaller --noconfirm --windowed --name PresenceCoach --collect-all sounddevice --collect-all google.genai --collect-all groq --hidden-import keyring.backends.Windows provider_mode.py
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" installer.iss
```

The resulting executable is unsigned unless you separately configure code signing.

## Verification

Run:

```powershell
python -m unittest discover -s tests -v
```

Automated tests cover coaching turn policy, Gemini transport behaviours, transcript
handling, Coach Practice review metrics, and deterministic Groq helper behaviour.
Hardware mocks are used for transport tests; these are not end-to-end live voice tests
and do not establish coaching quality.

Before calling this a release, test on a clean Windows 11 installation at common
Windows display scales, with real microphones/speakers, live Gemini and Groq quotas,
network failure, English sessions, pauses, interruption, transcript export, Coach
Practice scenarios, and ACC/PCC/MCC review generation. Test Hindi/Hinglish spoken
output with Gemini separately because current Groq Orpheus output is English-only.

## References

Presence uses ICF material as a developmental reference, not as an endorsement or
claim of assessment authority.

- 2025 ICF Core Competencies: https://coachingfederation.org/resource/icf-core-competencies/
- ACC Minimum Skills Requirements: https://coachingfederation.org/resource/acc-minimum-skills-requirements/
- PCC Minimum Skills Requirements: https://coachingfederation.org/resource/pcc-minimum-skills-requirements/
- MCC Minimum Skills Requirements: https://coachingfederation.org/resource/mcc-minimum-skills-requirements/
- Gemini Live API: https://ai.google.dev/gemini-api/docs/live-api
- Groq Quickstart: https://console.groq.com/docs/quickstart
- Groq Speech to Text: https://console.groq.com/docs/speech-to-text
- Groq Text to Speech: https://console.groq.com/docs/text-to-speech
- Groq supported models: https://console.groq.com/docs/models

See `reference/ICF-PRACTICE-DESIGN.md`, `COACHING-REVIEW.md`, and
`reference/AGILE-ORBIT-INTEGRATION.md` for the product's coaching-design notes and
manual review material.
