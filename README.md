# Presence Coach

Presence Coach is a Windows desktop application for practising professional coaching conversations with voice-enabled AI.

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
- Secure API-key storage through Windows Credential Manager

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
gemini-3.1-flash-live-preview
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

- Windows 10 or Windows 11, 64-bit
- Python 3.12
- Git
- A microphone and speakers or headphones
- A Google Gemini API key or Groq API key

Headphones are recommended to reduce microphone and speaker feedback.

### Setup

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

## First-time configuration

1. Open **Settings**.
2. Select **Google Gemini** or **Groq** as the AI provider.
3. Paste the API key for that provider.
4. Select the microphone and speaker or headphones.
5. Optionally enable secure key storage in Windows Credential Manager.
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
- Presence does not automatically save the session recording to disk.
- Exported Word and MP3 files are not encrypted by Presence and should be stored appropriately.
- Saved API keys use Windows Credential Manager through the operating-system keyring.

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

## References

Presence uses ICF material as a developmental reference, not as an endorsement or claim of assessment authority.

- [ICF Core Competencies](https://coachingfederation.org/resource/icf-core-competencies/)
- [ACC Minimum Skills Requirements](https://coachingfederation.org/resource/acc-minimum-skills-requirements/)
- [PCC Minimum Skills Requirements](https://coachingfederation.org/resource/pcc-minimum-skills-requirements/)
- [MCC Minimum Skills Requirements](https://coachingfederation.org/resource/mcc-minimum-skills-requirements/)
- [Gemini Live API](https://ai.google.dev/gemini-api/docs/live-api)
- [Gemini Live supported languages](https://ai.google.dev/gemini-api/docs/live-api/capabilities#supported-languages)
- [Groq Quickstart](https://console.groq.com/docs/quickstart)
- [Groq Speech to Text](https://console.groq.com/docs/speech-to-text)
- [Groq Text to Speech](https://console.groq.com/docs/text-to-speech)

## Status

Presence Coach is an experimental learning and coaching-practice project. Features and provider integrations may change as the project evolves.
