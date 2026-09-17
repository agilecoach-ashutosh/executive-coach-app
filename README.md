# Presence Coach — Windows desktop prototype

A Jarvis-inspired Windows desktop app for live coaching conversations.

Repository: https://github.com/agilecoach-ashutosh/executive-coach-app
Original implementation: no Mark-LIII source code or visual assets are copied.

**Status: runnable source prototype, not a verified Windows release.** The package
contains setup scripts and an installer build workflow, not a prebuilt EXE.
Live cloud sessions and real Windows microphone/speaker behaviour still need testing.

## Start on your Windows PC

1. Extract this ZIP into a permanent folder such as `C:\PresenceCoach`.
2. Install **Python 3.12 (64-bit)** from https://www.python.org/downloads/windows/
   including the Python launcher. It can coexist with Python 3.14; you do not need
   to uninstall your current Python. This build deliberately targets 3.12.
   Alternatively, in Terminal run `winget install -e --id Python.Python.3.12`.
3. Double-click **Setup.cmd**. It creates a private environment, installs packages
   and adds a desktop shortcut. Keep the folder in place afterwards.
4. Open **Presence Coach** from the desktop or double-click **Start.cmd**.
5. Open **Settings** and enter a Gemini API key from https://aistudio.google.com/apikey in the application.
   Do not put the key in GitHub, screenshots, transcripts or messages.
6. Choose devices in Settings, close it, tick consent and click **Begin conversation**. Say what you want
   to explore. Google processes the conversation, so internet and available Live
   API quota are required. This is not an offline application or a promise of free use.

The editable model defaults to `gemini-3.1-flash-live-preview`, the model selected
in the user-tested configuration. If your account cannot access it, select another
Live AUDIO model available to your account. A regular text model is not compatible.
The alternate entry is `gemini-3.8-live`.
Model availability is provider-controlled; changing the field cannot grant access.

## Amber voice-reactive interface

The main screen features an original procedural orb inspired by the supplied Jarvis
reference: rotating particles, animated filaments, a bright centre, and gentle movement.
Microphone amplitude drives the orb while listening; actual playback PCM amplitude
controls it while speaking. Idle motion is decorative, not a microphone indicator.
Use **Gentle motion** to reduce rotation and shaking.

Technical fields are in **Settings**. Hover over or keyboard-focus **How to get a key**
for instructions; click it for a persistent help dialog with Google AI Studio links.
Consent and session controls stay above the transcript. No extra dependencies are
required for this interface update.

### Updating an existing installation

Close the app. Download the repository ZIP using **Code → Download ZIP**, extract it,
and copy `app.py` and `engine.py` into your existing app folder, replacing both files.
Keep your `.venv` folder and launch using your existing `Start.cmd` or shortcut.
Saved keys remain in Windows Credential Manager. Select your preferred voice and
devices again in Settings. Settings other than the saved key reset on restart.

## During a conversation

| Control | Behaviour |
| --- | --- |
| Silence setting | Waits this long after detected speech before requesting a reply; default six seconds. |
| Take your time | Holds the current spoken turn through silence. Click **I'm ready** to submit it. |
| I'm ready | Finishes the current spoken turn. Does nothing if no turn has started. |
| Interrupt coach | Clears local playback and signals a new client turn; then speak. |
| Mute mic | Stops new microphone input and submits any already captured active turn. A reply may still play. |
| End | Disconnects audio and cloud processing; preserves the visible transcript. |
| Send | Sends typed input into the same connected conversation. |
| Save transcript | Opens a save dialog and writes a timestamped UTF-8 text file. |

**For private reflection without transmitting audio, use Mute or End.** Take your
time preserves the floor but is not a privacy mute: audio from the active turn
continues to stream. The app never stores raw recordings on disk.

The prototype uses **turn-based voice**, not automatic spoken interruption. Its mic
is ignored during coach playback to prevent speaker feedback. Use the interrupt
button to speak over the coach. Quiet-time detection uses local audio amplitude,
not semantic understanding; it can mistake a fan or nearby speech for your voice.
Use headphones and raise the threshold if background noise prevents a reply.
Lower it if soft speech is not detected. Settings apply on the next session.

Starting a new session resets model context. There is no hidden cross-session
memory or automatic reconnection. The app asks you to export unsaved text before
clearing it. If Google ends a session, export and start again; previous context
will not automatically carry over. A crash can lose text not yet exported.

Transcriptions arrive progressively but may be delayed, misrecognized or ordered
imperfectly by the provider. Interrupted coach text can contain generated words
that were never actually played. Exports include a note explaining this.

## Coaching behaviour

`coaching.py` contains the editable behavioural instructions. They ask the model
to remain in coaching mode without supplying solutions, establish the client's desired outcome, listen to their language, offer tentative
reflections, invite correction, ask one open question at a time, seek permission
before an exercise/challenge, and let clients choose their own actions.

Examples of intended quality (illustrative, not canned scripts):

- Client: “Everyone expects me to have the answer.”
  Coach: “What does having the answer represent for you?”
- Client: “I don't know. I need a moment.”
  Coach: “Take your time.” Then silence.
- Client: “Just tell me what I should do.”
  Coach: “I can help you think it through; the choice stays yours. What feels most important to you in this decision?”

This is an **AI reflection partner informed by ICF principles**. It is not an
ICF-certified coach, therapy, or a substitute for qualified human support. Prompt
instructions cannot guarantee question quality or crisis handling. Before offering
the app to clients, assess actual session transcripts and obtain appropriate consent.

## Privacy and keys

- Audio and typed conversation go to Google Gemini for processing; its terms apply.
- Conversations stay in app memory unless you export. Exported text is unencrypted;
  choose a suitable folder and manage access yourself.
- No screen capture, webcam, computer-control tools, background wake-word listener,
  analytics, automatic transcript uploads, or automatic disk recording are included.
- Keys are in memory by default. Opting to remember them uses the OS keyring
  (Windows Credential Manager on Windows). **Forget saved key** removes that entry.
- Removing the app does not automatically delete exported files or the credential;
  use Forget saved key before uninstalling if desired.

## Create an ordinary Windows installer

The included workflow is ready for a **executive-coach-app repository**. Open **Actions → Build Windows installer → Run workflow**. On a successful
run, download the **Presence-Coach-Windows** artifact and extract the setup EXE.

The workflow bundles Python and dependencies with PyInstaller, then packages them
with Inno Setup on a Windows runner. End users of that installer will not need
Python or a terminal. The resulting EXE is unsigned; signing and publisher identity
are release tasks. Only install builds from a source you trust. The workflow has
not yet been validated as a Windows release.

For a local build with Python 3.12 and Inno Setup 6 installed:

```powershell
py -3.12 -m pip install -r requirements.txt pyinstaller
py -3.12 -m PyInstaller --noconfirm --windowed --name PresenceCoach --collect-all sounddevice --collect-all google.genai --hidden-import keyring.backends.Windows app.py
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" installer.iss
```

## Verification and remaining release gates

Run `python -m unittest discover -s tests -v`.
Eleven automated tests cover playback amplitude returning to silence, silence timing, hold mode, noise gating, UTF-8 export, stopping playback,
muting queued audio, interrupt recovery, and processing all incoming audio parts.
Audio hardware is mocked in transport tests; these are not end-to-end voice tests.

Before calling this a release:

1. Build and launch the installer on a clean Windows 11 PC; verify setup, shortcut,
   audio permissions, selected devices, credentials, export, and uninstall.
2. Test live English/Hindi sessions, quiet speech, ambient noise, pauses, interrupt,
   quota errors and network loss. Verify client words do not get cut off.
3. Review at least ten realistic coaching conversations for agenda partnership,
   one-question pacing, non-leading language, assumptions, client-led brainstorming, closure,
   emotional distress and safe escalation. Record failures and iterate.
4. Check the new Settings window, consent controls, tooltips, and orb layout at 100%, 125% and 150% Windows display scaling. Current minimum
   window is 1080×700 logical pixels; sidebar settings scroll for shorter displays.
5. Freeze dependency versions after Windows validation, sign the installer and
   document the intended audience and support process.

Suggested next improvements: true speech interruption with echo cancellation,
semantic end-of-turn detection, adjustable speech speed, compact laptop layout,
verified session resumption, optional locally encrypted history, and coach-quality
evaluation. These are not implemented in this prototype.

## References

- Inspiration: https://github.com/FatihMakes/Mark-LIII
- ICF competencies: https://coachingfederation.org/credentialing/coaching-competencies/icf-core-competencies/
- Gemini Live: https://ai.google.dev/gemini-api/docs/live-api
- Voice and transcription API: https://ai.google.dev/gemini-api/docs/live-api/capabilities

The coaching prompt is original guidance, not a reproduction of ICF's competency text.

## Client-led coaching correction

The initial prompt allowed a switch to advice when a client requested ideas. A live
test showed that this supplied and anchored the client's options. That switch has
been removed. Brainstorming now invites the client's ideas; the coach must not add
a menu of solutions, disguise advice as a question, rank client options, or push
for an action. Necessary safety support remains available.

For existing installations, replace `coaching.py` and fully restart the app before
starting a fresh session. Existing live connections retain the previous prompt.
This is a prompt-level correction, not an enforced output filter. Automated audio
and turn tests do not establish coaching quality. Re-test the reported scenario
and the cases in `COACHING-REVIEW.md` with the actual Live model.

## Agile Orbit coaching content

The professional-coaching source pages and interactive JavaScript have been reviewed
and distilled into `coaching.py`, including client ownership, Empty Cup, listening,
metaphor, contracting, model restraint, tool use, ethics and closure. All 23 question
functions inform the runtime instructions. The 184 original website questions are
preserved for review in `reference/agile-orbit-question-bank.json`, not used as a
random question generator. See `reference/AGILE-ORBIT-INTEGRATION.md` for scope,
source revision, adaptations and limits. This is prompt guidance, not model training.

To install this behavioural update, replace **coaching.py**, close the app fully,
reopen it and start a fresh session. No reinstall or additional dependency is needed.

## Empathy and partnership refinement

The prompt now gives specific guidance for emotional openings, acknowledgement
without another question, accepting correction, consent before observations, and
respect for cultural and practical context. Client-generated choices remain central.
See [design and current ICF sources](reference/ICF-PRACTICE-DESIGN.md) and the expanded
[manual review scenarios](COACHING-REVIEW.md). These are design intentions; live
coaching quality has not been validated as PCC/MCC-equivalent.

For a source installation, update `coaching.py`, fully close the app, and start a
new session. A packaged executable needs rebuilding to include the new instructions.
