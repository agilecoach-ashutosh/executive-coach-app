# Presence Coach — Windows desktop coaching practice

Presence is a Windows desktop application for live professional-coaching practice.

It supports two experiences:

- **I am a Coachee** — Presence acts as the coach.
- **I am a Coach** — you coach a simulated professional coachee and review the session afterwards.

Presence currently supports:

- **Google Gemini** — native Gemini Live audio conversation.
- **Groq** — Whisper speech-to-text → Groq-hosted LLM → Orpheus text-to-speech.

Repository: https://github.com/agilecoach-ashutosh/executive-coach-app

---

## ⬇ Download Presence Coach for Windows

### [Download Presence Coach v0.2.0 (.exe)](https://github.com/agilecoach-ashutosh/executive-coach-app/releases/download/v0.2.0/Presence-Coach-Setup-0.2.0.exe)

**Windows 10/11 • 64-bit • Python not required**

> Windows SmartScreen may show **Unknown publisher** because the current installer is not code-signed. If you downloaded the installer from this official repository, choose **More info → Run anyway** to continue.

[View all releases](https://github.com/agilecoach-ashutosh/executive-coach-app/releases)

---

# Install Presence Coach on Windows

## Recommended — standalone installer

Normal users do **not** need to install Python, Git, pip, PowerShell packages, or download the source ZIP.

Presence is packaged with its own Python runtime and required libraries inside the Windows application.

### Step 1 — Download the installer

Download the latest installer from the link above or open the Releases page:

https://github.com/agilecoach-ashutosh/executive-coach-app/releases

Open the latest release and download the file named like:

`Presence-Coach-Setup-0.2.0.exe`

The exact version number may be newer.

### Step 2 — Install

1. Double-click `Presence-Coach-Setup-x.y.z.exe`.
2. Continue through the installer using **Next / Install**.
3. Click **Finish** when installation completes.
4. A **Presence Coach** shortcut is created on the Desktop and in the Start Menu.
5. Presence can be opened immediately from the final installer screen.

Presence installs for the current Windows user under Local AppData, so administrator access is normally not required.

### What the installer contains

The installer includes the packaged Presence application and its Python runtime, plus the libraries required for:

- Gemini Live
- Groq
- microphone and speaker audio
- Windows Credential Manager
- Word transcript/review export
- MP3 session-audio export
- the Presence Coach icon and UI resources

Python is **bundled with Presence**. The installer does not need to install a separate system-wide copy of Python.

> **Unsigned prototype:** until the installer is code-signed, Windows or antivirus products may identify it as an unknown publisher or give reputation warnings. Download builds only from this repository's official Releases page and do not run a file whose origin you cannot verify.

---

# First-time app setup

When Presence opens:

1. Open **⚙ Settings**.
2. Under **AI provider**, choose **Google Gemini** or **Groq**.
3. Paste the API key for the provider you selected.
4. Choose your **Microphone**.
5. Choose your **Speaker / headphones**.
6. Optionally enable **Remember key securely in Windows Credential Manager**.
7. Close Settings.
8. Choose **I am a Coachee** or **I am a Coach**.
9. Enable the provider consent checkbox.
10. Click **Begin**.

Headphones are recommended to reduce microphone/speaker feedback.

---

# Get a Google Gemini API key

1. Open Google AI Studio:
   https://aistudio.google.com/
2. Sign in with your Google account.
3. Open API Keys directly:
   https://aistudio.google.com/apikey
4. Click **Create API key**.
5. Select or create a Google Cloud project if Google asks.
6. Copy the generated key.
7. In Presence open **Settings → AI provider → Google Gemini**.
8. Paste it into **Gemini API key**.
9. Optionally enable secure key storage.

Do not put your API key in GitHub, screenshots, transcripts, or messages.

---

# Get a Groq API key

1. Open GroqCloud Console:
   https://console.groq.com/
2. Sign in or create an account.
3. Open API Keys directly:
   https://console.groq.com/keys
4. Click **Create API Key**.
5. Give it a name such as **Presence Coach**.
6. Create the key and copy it. Groq keys normally begin with `gsk_`.
7. In Presence open **Settings → AI provider → Groq**.
8. Paste it into **Groq API key**.
9. Optionally enable secure key storage.

The **ⓘ** button inside Presence also provides direct Gemini and Groq API-key links.

---

# Language support

| Provider in Presence | Spoken input | AI understanding | Spoken output in Presence |
| --- | --- | --- | --- |
| **Google Gemini Live** | 99 supported languages | Multilingual | 99 supported languages; native audio can switch languages during a conversation |
| **Groq** | 99+ languages through Whisper | Depends on the selected Groq chat model | English only in the current Presence configuration |

## Google Gemini

Gemini is the recommended provider in Presence for multilingual spoken coaching, including conversations that move between Hindi and English.

India-relevant supported languages include English, Hindi, Bengali, Assamese, Gujarati, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, Telugu, Urdu, Nepali, and Sindhi.

Current Gemini Live language information:
https://ai.google.dev/gemini-api/docs/live-api/capabilities#supported-languages

## Groq

Presence uses **Whisper Large V3 Turbo** by default for Groq speech recognition, which supports multilingual speech input.

The current Groq voice output in Presence uses:

`canopylabs/orpheus-v1-english`

Therefore Groq input can be multilingual, but the current spoken AI response is English.

Groq speech documentation:

https://console.groq.com/docs/speech-to-text

https://console.groq.com/docs/text-to-speech

---

# What the two modes do

## I am a Coachee

You bring a topic and Presence acts as the coach.

The coaching behaviour emphasizes client ownership, listening, concise reflections, non-leading exploration, one question at a time, consent before challenge/exercises, and client-generated learning/action.

Presence is an AI coaching practice tool. It is not a human therapist or an ICF-credentialed coach.

## I am a Coach

You become the coach. Presence becomes a simulated professional coachee.

You choose a workplace scenario and see only the client's presenting brief. The simulated coachee also receives hidden context so the conversation can unfold gradually rather than revealing the whole issue immediately.

This mode is designed for coaching practice and mentor-coaching discussion. An AI simulated coachee should not be represented as a genuine credential-submission client.

---

# Transcript, review and audio export

## Word transcript (.docx)

**Export transcript** creates a Microsoft Word document with a table using these columns:

| Speaker (Coach / Coachee) | Timestamp | Transcript |
| --- | --- | --- |
| Coach | 00:00:08 | What would make this conversation useful for you today? |
| Coachee | 00:00:17 | I want to understand why I keep avoiding this conversation. |

The timestamp is elapsed session time from the beginning of the session, not the computer clock.

## Session audio (.mp3)

Presence keeps the human microphone audio and AI playback audio in memory during the active session. The Session Review screen lets you explicitly export that conversation as an MP3 for reflection.

Presence does not automatically save session audio to disk.

## Coaching review (.docx)

After an **I am a Coach** session, Presence can generate a developmental review using an **ACC, PCC, or MCC** practice lens based on the current ICF Minimum Skills Requirements used by the app.

The exported Word review includes session metrics, behavior/evidence tables, development opportunities, patterns, practice edges, moments worth revisiting, and the bottom-line developmental summary.

The generated review is developmental AI feedback — **not an official ICF assessment, score, credential-readiness decision, or pass/fail result**.

---

# Coach Practice metrics

The Session Review screen currently includes descriptive measures such as:

- session duration
- Coach / Coachee transcript word share
- Coach and Coachee turns
- number of Coach questions
- stacked-question turns
- average Coach turn length
- longest Coach turn
- interruption notes

The speaking share is an estimate from transcript word count, not measured audio speaking time.

---

# Gemini and Groq pipelines

## Google Gemini

Gemini uses its Live API for native realtime audio conversation.

Current default Live model:

`gemini-3.1-flash-live-preview`

Provider-controlled model availability can change.

## Groq

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

---

# Update Presence Coach

For the standalone installer version:

1. Open the Releases page.
2. Download the newest `Presence-Coach-Setup-x.y.z.exe`.
3. Close Presence if it is running.
4. Run the new installer.
5. Install over the existing Presence Coach installation.

Your provider API key remains managed through Windows Credential Manager when you choose to remember it.

---

# Troubleshooting

### No microphone or speaker works

Open **Settings** in Presence and select the correct devices. Also check **Windows Settings → Privacy & security → Microphone** and make sure desktop applications are allowed to use the microphone.

### API key error

Use the **ⓘ** button in Presence to open the correct provider key page. Confirm that the selected provider matches the key you pasted.

### Export audio button is disabled

Start a new voice session using the current version, finish it normally, and open Session Review again. Typed messages have no microphone audio of their own.

### Windows says Unknown publisher

The current prototype installer is not code-signed. Verify that you downloaded it from the official GitHub Releases page. Public distribution should use a Windows code-signing certificate in a future release.

---

# Privacy and API keys

- With **Gemini**, live audio/text is processed by Google Gemini.
- With **Groq**, spoken turns are sent to Groq Whisper; conversation text is sent to the selected Groq chat model; AI reply text is sent to Groq Orpheus for speech generation.
- A post-session review sends the visible transcript and descriptive metrics only when you explicitly request the review.
- Transcript content and session audio are retained in application memory for the active session so you can choose whether to export them.
- Presence does not automatically save the session recording to disk.
- Exported DOCX and MP3 files are not encrypted by Presence. Store them appropriately for your coaching/privacy context.
- Saved API keys use Windows Credential Manager through the operating-system keyring.

Provider availability, free quotas, limits, pricing, models, and supported languages are controlled by Google and Groq and may change.

---

# Developer installation from source

The instructions below are for developers or contributors. **Normal users should use the standalone installer above.**

## 1. Install Python 3.12.10 64-bit

Direct official Windows installer:

https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe

Python release page:

https://www.python.org/downloads/release/python-31210/

Keep the Python Launcher enabled during installation.

## 2. Download or clone the repository

ZIP method:

1. Open https://github.com/agilecoach-ashutosh/executive-coach-app
2. Click **Code → Download ZIP**.
3. Extract the ZIP before running anything.

Git method:

```powershell
git clone https://github.com/agilecoach-ashutosh/executive-coach-app.git
cd executive-coach-app
```

## 3. Run developer setup

Double-click:

`Setup.cmd`

It creates `.venv`, installs `requirements.txt`, and creates a developer Desktop shortcut.

To start manually:

`Start.cmd`

---

# Build the standalone Windows installer

The GitHub Actions workflow is:

`.github/workflows/windows-build.yml`

It performs:

```text
Python 3.12.10 build environment
        ↓
Install project dependencies + PyInstaller
        ↓
Run automated tests
        ↓
PyInstaller bundles Presence + Python runtime
        ↓
Inno Setup creates one installer EXE
        ↓
Upload build artifact
        ↓
Optional GitHub Release
```

To build manually from GitHub:

1. Open **Actions** in this repository.
2. Choose **Build Windows installer**.
3. Click **Run workflow**.
4. Enter a version such as `0.2.0`.
5. Leave **Publish the installer to GitHub Releases** off for a test build, or turn it on for a release.
6. Download the generated artifact after the workflow completes.

Pushing a tag such as `v0.2.0` also builds the installer and publishes it to GitHub Releases automatically.

The generated user-facing file is:

`Presence-Coach-Setup-x.y.z.exe`

---

# Developer / source information

Current source structure:

```text
app.py                 Base Tkinter UI
engine.py              Gemini Live audio transport + session-audio capture
launch.py              Performance-optimized orb/dialog layer
practice_mode.py       Coach/Coachee role selection and simulated coachee mode
practice_review.py     Post-session metrics/review UI
provider_mode.py       Gemini/Groq provider selection
session_export.py      Word-table transcript + in-memory MP3 recorder/export helpers
session_export_mode.py Current application entry point and export UI layer
groq_engine.py         Groq Whisper → LLM → Orpheus voice engine + audio capture
coaching.py            Presence-as-coach behavioural instructions and Transcript model
scenarios.py           Simulated professional-coachee scenarios
reviewer.py            Metrics + ACC/PCC/MCC developmental review prompt
```

Run tests with:

```powershell
python -m unittest discover -s tests -v
```

Hardware mocks and export unit tests do not replace real microphone/speaker and live-provider testing.

---

# References

Presence uses ICF material as a developmental reference, not as an endorsement or claim of assessment authority.

- 2025 ICF Core Competencies: https://coachingfederation.org/resource/icf-core-competencies/
- ACC Minimum Skills Requirements: https://coachingfederation.org/resource/acc-minimum-skills-requirements/
- PCC Minimum Skills Requirements: https://coachingfederation.org/resource/pcc-minimum-skills-requirements/
- MCC Minimum Skills Requirements: https://coachingfederation.org/resource/mcc-minimum-skills-requirements/
- Gemini Live API: https://ai.google.dev/gemini-api/docs/live-api
- Gemini Live supported languages: https://ai.google.dev/gemini-api/docs/live-api/capabilities#supported-languages
- Groq Quickstart: https://console.groq.com/docs/quickstart
- Groq Speech to Text: https://console.groq.com/docs/speech-to-text
- Groq Text to Speech: https://console.groq.com/docs/text-to-speech
