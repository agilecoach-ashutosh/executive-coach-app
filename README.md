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
3. Click **Windows installer (64-bit)**.
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
   - install Word transcript and MP3 export support,
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

# Language support

Language support is different for Gemini and Groq because the two providers use different voice pipelines.

| Provider in Presence | Spoken input | AI understanding | Spoken output in Presence |
| --- | --- | --- | --- |
| **Google Gemini Live** | **99 supported languages** | Multilingual | **99 supported languages**; native audio can switch languages naturally during a conversation |
| **Groq** | **99+ languages** through Whisper | Multilingual capability depends on the selected Groq chat model | **English only in the current Presence configuration** |

## Google Gemini language support

Google's current Gemini Live documentation lists **99 supported languages**. Native audio models can automatically use the appropriate language and can switch between languages naturally during the same conversation.

This makes Gemini the recommended provider in Presence when you want multilingual spoken coaching.

Languages especially relevant for users in India include:

- English
- Hindi
- Bengali
- Assamese
- Gujarati
- Kannada
- Malayalam
- Marathi
- Odia
- Punjabi
- Tamil
- Telugu
- Urdu
- Nepali
- Sindhi

Gemini Live also supports many other languages including Arabic, Chinese, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish, Thai, Turkish, Ukrainian, Vietnamese, and many more.

For Google's complete current list of supported Gemini Live languages, see:

https://ai.google.dev/gemini-api/docs/live-api/capabilities#supported-languages

**Hinglish / mixed-language conversation:** Gemini native audio can switch between supported languages naturally, so it is currently the better Presence option for conversations that move between Hindi and English.

## Groq language support

Presence uses **Groq Whisper Large V3 Turbo** by default for speech recognition. Groq documents Whisper Large V3 Turbo as supporting **99+ languages** for transcription.

That means Presence can accept speech in many languages through Groq, including Hindi and many other Indian and international languages.

However, the current Groq voice pipeline in Presence uses:

`canopylabs/orpheus-v1-english`

Therefore:

- **Speech input:** multilingual through Whisper
- **Conversation model:** may understand and generate multiple languages depending on the selected Groq model
- **Spoken AI response:** **English only in the current Presence implementation**

Groq also provides a separate **Saudi Arabic Orpheus TTS model**, but Presence does **not** currently enable that model.

For Groq's current speech documentation, see:

https://console.groq.com/docs/speech-to-text

https://console.groq.com/docs/text-to-speech

### Which provider should I use for language?

- For **English-only coaching**, Gemini or Groq can be used.
- For **Hindi, Hinglish, Marathi, Tamil, Telugu, Bengali, Gujarati, Punjabi, Urdu, or other multilingual spoken sessions**, use **Gemini** for the best current Presence experience.
- Groq can still transcribe multilingual speech, but Presence currently speaks the Groq response back in English.

Provider language capabilities can change over time, so the linked Google and Groq documentation is the source of truth for current provider support.

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

# Transcript and audio export

Presence can export two reflection artifacts after a session.

## Word transcript (.docx)

**Export transcript** now creates a Microsoft Word `.docx` file instead of a plain-text transcript.

The Word document contains one table with these three headers:

| Speaker (Coach / Coachee) | Timestamp | Transcript |
| --- | --- | --- |
| Coach | 00:00:08 | What would make this conversation useful for you today? |
| Coachee | 00:00:17 | I want to understand why I keep avoiding this conversation. |

The timestamp is **elapsed session time from the beginning of the session**, not the computer's clock time. It uses `HH:MM:SS`, so a row at two minutes and seventeen seconds appears as `00:02:17`.

Only Coach and Coachee dialogue is written into the Word table. Internal/session-note rows are not treated as speakers.

## Session audio (.mp3)

For sessions started with the current export-enabled version, Presence keeps the human microphone audio and the AI audio that was actually played **in memory during that session**.

After an **I am a Coach** session ends, the Session Review screen provides:

**Export session audio (.mp3)**

The exported MP3 combines both sides of the conversation on the original session timeline so it can be replayed for reflection or mentor-coaching discussion.

Presence does not automatically save session audio. The MP3 is written only when you explicitly choose **Export session audio (.mp3)**.

Typed messages naturally have no spoken audio of their own, although they still appear in the Word transcript.

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

The review screen also lets you:

- **Export transcript (.docx)**
- **Export session audio (.mp3)**
- **Export review**

You can request a developmental review against an **ACC**, **PCC**, or **MCC** practice lens.

The review uses only the visible transcript, visible scenario brief, and descriptive metrics. It does not receive the simulated client's hidden persona.

The generated review is developmental AI feedback — **not an official ICF assessment, score, credential-readiness decision, or pass/fail result**.

---

# Gemini and Groq differences

## Google Gemini

Gemini uses its Live API for native realtime audio conversation.

The current default Live model is:

`gemini-3.1-flash-live-preview`

Gemini Live currently supports 99 languages and is the preferred provider for multilingual spoken sessions in Presence.

Provider-controlled model and language availability can change.

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

Groq Whisper supports 99+ languages for spoken input. The Orpheus voice used by Presence is currently English-only, so Gemini is currently the better choice when spoken Hindi/Hinglish or other non-English output is important.

---

# Update an existing installation

If you originally downloaded Presence as a ZIP, the simplest update method is:

1. Download the latest ZIP from GitHub again.
2. Extract it.
3. Run **Setup.cmd** again.
4. Start Presence from the newly created Desktop shortcut.

If you use Git, run:

```powershell
git pull
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then fully close Presence and reopen it.

**Important:** Word and MP3 export add new Python packages, so existing installations must either rerun **Setup.cmd** or run the dependency-install command above after pulling this update.

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

### Export audio button is disabled

Audio is available only for a session that was started after the export-enabled version of Presence was launched. Start a new session, finish it normally, and open Session Review again.

---

# Privacy and API keys

- With **Gemini**, live audio/text is processed by Google Gemini.
- With **Groq**, spoken turns are sent to Groq Whisper; conversation text is sent to the selected Groq chat model; AI reply text is sent to Groq Orpheus for speech generation.
- A post-session review sends the visible transcript and descriptive metrics only when you explicitly request the review.
- Transcript content and session audio are retained in application memory for the active session so you can choose whether to export them.
- Presence does **not** automatically save the session recording to disk.
- **Export transcript** writes a Word `.docx` file only when you choose to export.
- **Export session audio** writes an MP3 file only when you choose to export.
- **Export review** writes the generated review when you choose to export it.
- Exported DOCX, MP3, and review files are not encrypted by Presence. Store them appropriately for your coaching/privacy context.
- Saved API keys use the operating-system keyring / Windows Credential Manager.

Provider availability, free quotas, limits, pricing, models, and supported languages are controlled by Google and Groq and may change.

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

Run automated tests with:

```powershell
python -m unittest discover -s tests -v
```

The Windows build workflow packages `session_export_mode.py` using PyInstaller and Inno Setup. Hardware mocks and export unit tests do not replace real microphone/speaker and live-provider testing.

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
