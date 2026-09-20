# Presence Coach

Presence Coach is a Windows and macOS desktop application for practising professional coaching conversations with voice-enabled AI.

It provides two experiences:

- **I am a Coachee** — bring a topic and let Presence act as the coach.
- **I am a Coach** — coach a simulated professional client, then review the session.

> [!IMPORTANT]
> Presence Coach is an educational and practice tool. It is not a therapist, an ICF-credentialed coach, an official ICF assessment platform, or a substitute for professional mental-health support.

## Why Presence Coach?

**You can talk to any AI. Presence helps you practice coaching.**

General AI voice assistants can already hold useful coaching-style conversations, especially with a carefully written prompt. Presence Coach is designed for a narrower job: **deliberate practice of professional coaching**. It combines realistic practice conversations, coaching-specific roles, evidence from the transcript, developmental ACC/PCC/MCC lenses, session metrics, and review exports in one repeatable workflow.

| General AI voice chat | Presence Coach |
| --- | --- |
| General-purpose conversation | Purpose-built coaching practice environment |
| Coaching or coachee role usually needs to be explained in the prompt | Built-in **I am a Coachee** and **I am a Coach** modes |
| Practice scenario and persona usually need to be created manually | Ready-to-use workplace scenarios with hidden coachee context |
| AI may reveal too much of the simulated persona unless carefully instructed | Simulated coachee is designed to reveal context gradually through the conversation |
| Coaching framework must usually be requested or supplied | Built-in developmental **ACC, PCC, and MCC** practice lenses |
| Detailed behavior-by-behavior review requires additional prompting | ACC review evaluates **A3.1–A8.3** behavior by behavior using the configured developmental framework |
| Evidence and timestamps must usually be requested separately | Review observations are tied back to exact transcript timestamps where evidence exists |
| Session metrics are not normally part of the conversation workflow | Coach/Coachee word share, turns, questions, stacked questions, turn length, and interruption notes |
| Transcript review and document creation require extra steps | Annotated transcript and developmental Word review are generated from the same session |
| Useful for a one-off conversation | Designed for repeat practice, reflection, and discussion with a mentor coach |

Presence does not depend on having a uniquely capable language model. Its value is the **practice system around the model**: practice a conversation, inspect the evidence, identify development areas, and practise again.

## Key capabilities

- Live voice conversations using Google Gemini or Groq
- English and multilingual speech support, depending on the selected provider
- Coachee mode with non-directive, client-centred coaching behaviour
- Coach-practice mode with a searchable Scenario Library, scenario packs, difficulty levels, practice-focus filters, and Surprise Me
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
- Python 3.12 (You can download easily from python org official website)
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

Clone the repository:

```bash
git clone https://github.com/agilecoach-ashutosh/executive-coach-app.git
cd executive-coach-app
```

Run:

```text
Setup-Mac.command
```

The setup script creates a local virtual environment and installs the dependencies from `requirements.txt`.

Start the application with:

```text
Start-Mac.command
```

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

Presence uses a local-first session model, but the selected cloud AI provider still processes the conversation.

- With **Gemini**, live audio/text and generated responses are processed by Google Gemini under the user's own API project.
- With **Groq**, spoken turns are sent to Groq Whisper, conversation text is sent to the selected Groq chat model, and reply text is sent to Groq Orpheus for speech generation.
- A post-session review sends the visible transcript and descriptive metrics only when the user explicitly requests the review and provider authorization is enabled.
- Transcript content and captured session audio remain in application memory so the user can decide whether to export them.
- Presence does not automatically save the session recording to disk.
- **Privacy & data use** in the app explains the current data flow and includes **Discard current session data** to clear the in-memory transcript/audio after a session.
- Provider authorization is session-scoped. It resets after a completed session and when the selected provider changes. Withdrawing it during a live session ends the connection.
- Exported Word and MP3 files are not encrypted by Presence and should be stored appropriately.
- Saved API keys use Windows Credential Manager or macOS Keychain through the operating-system keyring.
- Presence is intended for adults aged **18 or older**.

For real-client or organizational use, the user remains responsible for an appropriate lawful basis, privacy notice, recording permission where required, confidentiality obligations, provider-plan selection, retention, and international-transfer requirements.

See **[PRIVACY.md](PRIVACY.md)** for the full privacy and data-processing notice, including Gemini/Groq retention information, GDPR-oriented guidance, deletion boundaries, and individual-rights handling.

> [!IMPORTANT]
> The project is designed with privacy-by-design principles in mind, but it does not claim blanket or certified GDPR compliance. Compliance depends on deployment, provider plan/settings, the data entered, and the user's legal/organizational context.

## Project structure

| File | Purpose |
| --- | --- |
| `app.py` | Base Tkinter interface |
| `engine.py` | Gemini Live transport and session-audio capture |
| `launch.py` | Performance-optimized orb and dialog layer |
| `practice_mode.py` | Role selection and simulated-coachee mode |
| `practice_review.py` | Post-session metrics and review interface |
| `provider_mode.py` | Gemini and Groq provider selection |\n| `privacy_mode.py` | Session-scoped provider authorization, privacy notice UI, and in-memory discard control |
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

- Use Presence only with adults aged 18 or older.\n- Obtain appropriate consent before recording or processing another person's voice or coaching conversation.
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
