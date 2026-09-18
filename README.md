# Presence Coach

Presence Coach is a Windows and macOS desktop application for practising professional coaching conversations with voice-enabled AI.

It provides two experiences:

- **I am a Coachee** — bring a topic and let Presence act as the coach.
- **I am a Coach** — coach a simulated professional client, then review the session.

> [!IMPORTANT]
> Presence Coach is an educational and practice tool. It is not a therapist, an ICF-credentialed coach, an official ICF assessment platform, or a substitute for professional mental-health support.

## Key capabilities

- Live voice conversations using Google Gemini or Groq
- English and multilingual speech support, depending on the selected provider
- Coachee mode with non-directive, client-centred coaching behaviour
- Coach-practice mode with realistic workplace scenarios
- Developmental review through ACC, PCC, or MCC practice lenses
- Session transcript export to Microsoft Word
- Optional session-audio export to MP3
- Secure API-key storage through the operating system credential store

## How the two modes work

### I am a Coachee

You bring a topic and Presence acts as the coach. Its coaching behaviour emphasizes:

- client ownership of the topic and outcome
- attentive listening and concise reflections
- one clear question at a time
- non-leading exploration
- consent before offering a challenge, observation, or exercise
- client-generated learning and action

### I am a Coach

You act as the coach while Presence plays a simulated professional coachee.

You select a workplace scenario and receive only the client's presenting brief. Presence also receives hidden scenario context, allowing the conversation to unfold gradually instead of revealing the full issue at the beginning.

After the session, Presence can generate developmental feedback using an ACC, PCC, or MCC practice lens. This feedback is intended for reflection and mentor-coaching discussion; it is not an official assessment or credential-readiness decision.

## AI providers

| Provider | Speech input | Conversation | Speech output |
| --- | --- | --- | --- |
| **Google Gemini Live** | Multilingual | Native real-time audio | Multilingual |
| **Groq** | Multilingual through Whisper | Text-based LLM pipeline | English in the current configuration |

Gemini is the recommended option for multilingual coaching, including conversations that move between Hindi and English.

### Gemini pipeline

Gemini uses its Live API for native real-time audio conversation.

Current default model:

```text
gemini-3.8-live
```

### Groq pipeline

```text
Microphone
    ↓
whisper-large-v3-turbo
Speech to text
    ↓
openai/gpt-oss-120b
Coaching response
    ↓
canopylabs/orpheus-v1-english
Text to speech
    ↓
Speaker or headphones
```

Provider-controlled models, quotas, availability, pricing, and supported languages may change.

## Run from source

### Requirements

- Windows 10 or Windows 11, 64-bit; or a supported Intel/Apple Silicon Mac
- Python 3.12
- Git
- A microphone and speakers or headphones
- A Google Gemini API key or Groq API key

Headphones are recommended to reduce microphone and speaker feedback.

### Windows setup

Clone the repository:

```powershell
git clone https://github.com/agilecoach-ashutosh/executive-coach-app.git
cd executive-coach-app
```

Run:

```text
Setup.cmd
```

The setup script creates a local virtual environment, installs the dependencies from `requirements.txt`, and creates a developer shortcut.

Start the application with:

```text
Start.cmd
```

### macOS setup

Install Python 3.12 from [python.org](https://www.python.org/downloads/macos/). The official installer includes the Tk support required by the interface.

Clone the repository, or download and extract its ZIP file. In the project folder, double-click:

```text
Setup-Mac.command
```

When setup finishes, start the application by double-clicking:

```text
Start-Mac.command
```

If macOS blocks a command file downloaded from the internet, Control-click it, select **Open**, and confirm **Open**. On the first coaching session, allow microphone access when macOS requests it. The permission can later be changed under **System Settings → Privacy & Security → Microphone**.

## First-time configuration

1. Open **Settings**.
2. Select **Google Gemini** or **Groq** as the AI provider.
3. Paste the API key for that provider.
4. Select the microphone and speaker or headphones.
5. Optionally enable secure key storage in Windows Credential Manager or macOS Keychain.
6. Close Settings.
7. Choose **I am a Coachee** or **I am a Coach**.
8. Review and select the provider-consent checkbox.
9. Select **Begin**.

The information button inside Presence opens the official API-key pages for the supported providers.

> [!CAUTION]
> Never commit API keys to the repository or include them in screenshots, transcripts, issues, or messages.

## Session outputs

### Transcript

**Export transcript** creates a Microsoft Word document with the following structure:

| Speaker | Timestamp | Transcript |
| --- | --- | --- |
| Coach | 00:00:08 | What would make this conversation useful for you today? |
| Coachee | 00:00:17 | I want to understand why I keep avoiding this conversation. |

The timestamp is elapsed session time, not the computer clock.

### Session audio

During an active session, Presence keeps the human microphone audio and AI playback audio in memory. The Session Review screen allows the user to explicitly export that conversation as an MP3.

Presence does not automatically save session audio to disk.

### Coaching review

After an **I am a Coach** session, Presence can create a developmental Word report containing:

- session metrics
- behaviour and evidence tables
- development opportunities
- recurring patterns
- practice edges
- moments worth revisiting
- a bottom-line developmental summary

The review is AI-generated developmental feedback, not an official ICF score, assessment, pass/fail result, or credential decision.

## Coach-practice metrics

The Session Review screen includes descriptive measures such as:

- session duration
- Coach and Coachee transcript word share
- Coach and Coachee turns
- number of Coach questions
- stacked-question turns
- average Coach turn length
- longest Coach turn
- interruption notes

Speaking share is estimated from transcript word counts; it is not measured audio speaking time.

## Privacy and data handling

- With **Gemini**, live audio and text are processed by Google Gemini.
- With **Groq**, spoken turns are sent to Groq Whisper, conversation text is sent to the selected Groq chat model, and reply text is sent to Groq Orpheus for speech generation.
- A post-session review sends the visible transcript and descriptive metrics only when the user explicitly requests the review.
- Transcript content and session audio remain in application memory during the active session so the user can decide whether to export them.
- The Groq speech pipeline uploads and plays WAV data from memory; it does not create temporary session-audio files.
- Presence does not automatically save the session recording to disk.
- Exported Word and MP3 files are not encrypted by Presence and should be stored appropriately.
- Saved API keys use Windows Credential Manager or macOS Keychain through the operating-system keyring.

Review the policies and data-handling terms of the selected AI provider before using real or sensitive coaching information.

## Project structure

| File | Purpose |
| --- | --- |
| `app.py` | Base Tkinter interface |
| `engine.py` | Gemini Live transport and session-audio capture |
| `launch.py` | Performance-optimized orb and dialog layer |
| `practice_mode.py` | Role selection and simulated-coachee mode |
| `practice_review.py` | Post-session metrics and review interface |
| `provider_mode.py` | Gemini and Groq provider selection |
| `session_export.py` | Transcript and in-memory audio export helpers |
| `session_export_mode.py` | Current application entry point and export interface |
| `groq_engine.py` | Groq speech-to-text, LLM, and text-to-speech pipeline |
| `coaching.py` | Coach behaviour instructions and transcript model |
| `scenarios.py` | Simulated professional-coachee scenarios |
| `reviewer.py` | Metrics and developmental-review prompt |

## Testing

Run the automated test suite with:

```powershell
python -m unittest discover -s tests -v
```

Automated tests and hardware mocks do not replace real microphone, speaker, and live-provider testing.

## Troubleshooting

### Microphone or speaker is unavailable

Select the correct devices in Presence settings. In Windows, also open **Settings → Privacy & security → Microphone** and allow desktop applications to use the microphone.

### API-key error

Confirm that the selected provider matches the key entered in Settings. Use the information button in Presence to open the provider's official API-key page.

### Audio export is unavailable

Start and finish a new voice session, then open Session Review. Typed messages do not contain microphone audio.

## Responsible use

- Obtain appropriate consent before recording or processing another person's voice or coaching conversation.
- Do not submit confidential client information unless your privacy, contractual, and organizational requirements permit it.
- Treat generated reviews as developmental prompts that require human judgment.
- Do not represent a simulated-coachee session as a genuine credential-submission recording.
- Use qualified human support for mental-health crises, clinical care, safeguarding concerns, or other high-risk situations.

## Content and coaching references

Presence Coach is an original educational/practice application. The coaching behaviour, developmental-review logic, and observation-report design are informed by the following professional-coaching sources. These references do **not** imply ICF endorsement, accreditation, assessment authority, or that Presence can replace a qualified human coach, mentor coach, or ICF assessor.

### ICF professional coaching foundations

- [2025 ICF Core Competencies](https://coachingfederation.org/resource/icf-core-competencies/) — foundation for ethical practice, agreements, trust and safety, presence, active listening, evoking awareness, and client growth.
- [2025 ICF Code of Ethics](https://coachingfederation.org/credentialing/coaching-ethics/icf-code-of-ethics/) — reference for ethical boundaries, professional role clarity, confidentiality, integrity, and responsible coaching practice.
- [ICF Mentor Coaches resource hub](https://coachingfederation.org/audience-type/mentor-coaches/) — official ICF collection of mentor-coaching observation and competency-review resources.

### Credential-level developmental review references

- [ACC Minimum Skills Requirements](https://coachingfederation.org/resource/acc-minimum-skills-requirements/) — developmental ACC evidence lens used by the review system.
- [PCC Minimum Skills Requirements](https://coachingfederation.org/resource/pcc-minimum-skills-requirements/) — developmental PCC evidence lens used by the review system.
- [MCC Minimum Skills Requirements](https://coachingfederation.org/resource/mcc-minimum-skills-requirements/) — developmental MCC mastery lens used by the review system.
- [ACC Session Observation Form](https://coachingfederation.org/resource/acc-session-observation-form/) — informs the ACC Word-review observation structure, evidence-by-timestamp approach, Competency 1 qualifiers, Competency 2 limitation, and the Competencies 3–8 rating scale.
- [PCC Session Observation Form](https://coachingfederation.org/resource/pcc-session-observation-form/) — official reference for PCC mentor-coaching session observation and evidence documentation.
- [MCC Session Observation Form](https://coachingfederation.org/resource/mcc-session-observation-form/) — official reference for MCC mentor-coaching session observation and evidence documentation.

### Owner-authored coaching content

- [Agile Orbit — Professional Coaching](https://agilecoach-ashutosh.github.io/agile-orbit/coaching/professional-coaching.html) — owner-authored professional-coaching material used as a content reference for Presence coaching behaviour, client ownership, session agreements, listening, questions, coaching mindset, ethics, reflection tools, and closure.
- [Agile Orbit source repository](https://github.com/agilecoach-ashutosh/agile-orbit) — versioned source for the owner-authored coaching content referenced during Presence design.
- [Presence: Agile Orbit integration notes](reference/AGILE-ORBIT-INTEGRATION.md) — documents which Agile Orbit ideas were adapted into Presence and the deliberate product boundaries applied.
- [Presence: ICF practice-design notes](reference/ICF-PRACTICE-DESIGN.md) — documents how ICF sources informed the coaching-practice design without claiming credential equivalence.
- [Presence: Agile Orbit source manifest](reference/agile-orbit-source-manifest.json) — records the source snapshot used when the Agile Orbit coaching material was reviewed for Presence.

Technical provider/API documentation is kept in the relevant setup and provider sections of this README rather than in this content-reference library.

## Status

Presence Coach is an experimental learning and coaching-practice project. Features and provider integrations may change as the project evolves.
