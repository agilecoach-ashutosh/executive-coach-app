# Presence Coach — Windows desktop prototype

Presence is a Windows desktop application for live professional-coaching practice.

It supports two experiences:

- **I am a Coachee** — Presence acts as the coach.
- **I am a Coach** — you coach a simulated professional coachee and can review the session afterwards.

Presence currently supports:

- **Google Gemini** — native Gemini Live audio conversation.
- **Groq** — Whisper speech-to-text → Groq-hosted LLM → Orpheus text-to-speech.

Repository: https://github.com/agilecoach-ashutosh/executive-coach-app

> **Prototype:** this is runnable source code, not a verified production Windows release.

---

# Install Presence Coach on a Windows desktop

You do **not** need to use Terminal, PowerShell, Git, or write any Python code for a first-time installation.

## Pre-step 1 — Install Python 3.12.10 (64-bit)

Presence currently uses **Python 3.12.10, 64-bit**.

### Option A — easiest: direct Windows 64-bit installer

Click this official Python installer:

https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe

When the Python installer opens:

1. Tick **Add python.exe to PATH** if that option is shown.
2. Make sure the **Python Launcher / py launcher** remains enabled.
3. Click **Install Now**.
4. Continue with **Yes / Next / Install** when Windows asks.
5. Wait until Python says the installation was successful.
6. Close the Python installer.

### Option B — use the Python download page

Open:

https://www.python.org/downloads/release/python-31210/

Then:

1. Scroll down to **Files**.
2. Find the **Windows** section.
3. Click **Windows installer (64-bit)** — this is the recommended Windows installer.
4. Run the downloaded `.exe` and complete the installation as described above.

**Why Python 3.12.10?** It is the last Python 3.12 release that provides an official Windows binary installer. Later Python 3.12 security releases are source-only.

---

## Pre-step 2 — Download Presence Coach from GitHub

1. Open the Presence Coach repository:

   https://github.com/agilecoach-ashutosh/executive-coach-app

2. Click the green **Code** button.
3. Click **Download ZIP**.
4. Wait for `executive-coach-app-main.zip` to download.

Usually the ZIP will be in your **Downloads** folder.

---

# Install it on your Desktop

## Step 1 — Extract the ZIP

1. Open your **Downloads** folder.
2. Find `executive-coach-app-main.zip`.
3. Right-click it and choose **Extract All...**.
4. Choose your **Desktop** as the destination.
5. Click **Extract**.
6. Open the extracted `executive-coach-app-main` folder on your Desktop.

Do **not** run Presence directly from inside the ZIP file. Extract it first.

---

## Step 2 — Run Setup.cmd

Inside the extracted Presence Coach folder:

1. Find **Setup.cmd**.
2. Double-click **Setup.cmd**.
3. A Command Prompt window will open automatically.
4. Presence will:
   - check Python 3.12,
   - create its own `.venv` environment,
   - install all required packages,
   - install Gemini/Groq dependencies,
   - create a **Presence Coach** shortcut on your Desktop.
5. Internet access is required during this setup.
6. Wait until you see:

   `Setup complete. Use the Presence Coach desktop shortcut or Start.cmd.`

7. Press any key if prompted and close the setup window.

The first setup may take a few minutes because Python packages need to be downloaded.

---

## Step 3 — Open Presence Coach

After Setup finishes, you have two ways to start the app:

### Recommended

Double-click the new **Presence Coach** shortcut on your Windows Desktop.

### Alternative

Open the extracted Presence folder and double-click:

`Start.cmd`

You should now see the Presence Coach interface.

---

# First-time app setup

When Presence opens:

1. Open **⚙ Settings**.
2. Under **AI provider**, choose:
   - **Google Gemini**, or
   - **Groq**.
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
3. Open the API Keys page directly:

   https://aistudio.google.com/apikey

4. Click **Create API key**.
5. Select or create a Google Cloud project if Google asks.
6. Copy the generated API key.
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

# What the two modes do

## I am a Coachee

You bring a topic and Presence acts as the coach.

`coaching.py` contains the coaching behaviour. It emphasizes client ownership, listening, concise reflections, non-leading exploration, one question at a time, consent before challenge/exercises, and client-generated learning/action.

Presence is an AI coaching practice tool. It is not a human therapist or an ICF-credentialed coach.

## I am a Coach

You become the coach. Presence becomes a simulated professional coachee.

You choose a workplace scenario and see only the client's presenting brief. The simulated coachee also receives hidden context so the conversation can unfold gradually rather than revealing the whole issue immediately.

This mode is designed for coaching practice and mentor-coaching discussion. An AI simulated coachee should not be represented as a genuine credential-submission client.

---

# Coach Practice review

After an **I am a Coach** session ends, Presence opens a Session Review screen.

It currently shows descriptive metrics such as:

- session duration,
- Coach / Coachee transcript word share,
- Coach and Coachee turns,
- number of Coach questions,
- stacked-question turns,
- average Coach turn length,
- longest Coach turn,
- interruption notes.

You can also request a developmental review against an **ACC**, **PCC**, or **MCC** practice lens.

The review uses only the visible transcript, visible scenario brief, and descriptive metrics. It does not receive the simulated client's hidden persona.

The generated review is developmental AI feedback — **not an official ICF assessment, score, credential-readiness decision, or pass/fail result**.

---

# Gemini and Groq differences

## Google Gemini

Gemini uses its Live API for native realtime audio conversation.

The current default Live model is:

`gemini-3.1-flash-live-preview`

Provider-controlled model availability can change.

## Groq

The default Groq voice pipeline is:

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

Groq Whisper and the conversation model are multilingual. The Orpheus voice used by Presence is currently English-only, so Gemini is currently the better choice when spoken Hindi/Hinglish output is important.

---

# Update an existing installation

If you originally downloaded Presence as a ZIP, the simplest update method is:

1. Download the latest ZIP from GitHub again.
2. Extract it.
3. Run **Setup.cmd** again.
4. Start Presence from the newly created Desktop shortcut.

If you use Git, you can instead run:

```powershell
git pull
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then fully close Presence and reopen it.

---

# Troubleshooting installation

### Setup says Python 3.12 is missing

Install **Python 3.12.10 64-bit** using the link at the top of this README, then run `Setup.cmd` again.

### Presence shortcut was not created

Open the extracted Presence folder and double-click `Start.cmd`.

### Start.cmd says "Run Setup.cmd first"

`Setup.cmd` has not completed successfully. Run it again and read the error shown in the Command Prompt window.

### No microphone or speaker works

Open **Settings** in Presence and select the correct devices. Also check Windows **Settings → Privacy & security → Microphone** and make sure desktop applications are allowed to use the microphone.

### API key error

Use the **ⓘ** button in Presence to open the correct provider key page. Confirm that the selected provider matches the key you pasted.

---

# Privacy and API keys

- With **Gemini**, live audio/text is processed by Google Gemini.
- With **Groq**, spoken turns are sent to Groq Whisper; conversation text is sent to the selected Groq chat model; AI reply text is sent to Groq Orpheus for speech generation.
- A post-session review sends the visible transcript and descriptive metrics only when you explicitly request the review.
- Conversations remain in application memory unless exported.
- Exported transcript/review files are ordinary unencrypted text files.
- Presence does not currently save raw session recordings.
- Saved API keys use the operating-system keyring / Windows Credential Manager.

Provider availability, free quotas, limits, and pricing are controlled by Google and Groq and may change.

---

# Developer / source information

Current source structure:

```text
app.py              Base Tkinter UI
engine.py           Gemini Live audio transport
launch.py           Performance-optimized orb/dialog layer
practice_mode.py    Coach/Coachee role selection and simulated coachee mode
practice_review.py  Post-session metrics/review UI
provider_mode.py    Gemini/Groq provider selection and current application entry point
groq_engine.py      Groq Whisper → LLM → Orpheus voice engine
coaching.py         Presence-as-coach behavioural instructions and Transcript model
scenarios.py        Simulated professional-coachee scenarios
reviewer.py         Metrics + ACC/PCC/MCC developmental review prompt
```

Run automated tests with:

```powershell
python -m unittest discover -s tests -v
```

The Windows build workflow packages `provider_mode.py` using PyInstaller and Inno Setup. Hardware mocks in automated tests do not replace real microphone/speaker and live-provider testing.

---

# References

Presence uses ICF material as a developmental reference, not as an endorsement or claim of assessment authority.

- 2025 ICF Core Competencies: https://coachingfederation.org/resource/icf-core-competencies/
- ACC Minimum Skills Requirements: https://coachingfederation.org/resource/acc-minimum-skills-requirements/
- PCC Minimum Skills Requirements: https://coachingfederation.org/resource/pcc-minimum-skills-requirements/
- MCC Minimum Skills Requirements: https://coachingfederation.org/resource/mcc-minimum-skills-requirements/
- Gemini Live API: https://ai.google.dev/gemini-api/docs/live-api
- Groq Quickstart: https://console.groq.com/docs/quickstart
- Groq Speech to Text: https://console.groq.com/docs/speech-to-text
- Groq Text to Speech: https://console.groq.com/docs/text-to-speech
