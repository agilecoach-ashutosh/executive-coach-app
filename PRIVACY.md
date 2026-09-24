# Presence Coach Privacy & Data Processing Notice

**Last updated: 20 September 2026**

Presence Coach is a local desktop coaching-practice application. This notice explains what the current open-source build does with voice, transcripts, API keys, exports, and AI-provider processing.

This notice is designed to support transparent, privacy-conscious use. It is **not a certification of GDPR compliance**. Compliance depends on how Presence is deployed, which AI-provider plan and settings are used, what information is entered, and the legal/organizational context of the person or organization using it.

## 1. Scope

This notice covers the Presence Coach desktop application in this repository.

The current project does **not** operate:

- a Presence user-account service;
- a maintainer-operated cloud database of coaching sessions;
- a central transcript or recording store;
- application analytics or telemetry that sends coaching-session content to the project maintainer.

Running the application does, however, send session information to the cloud AI provider selected by the user.

## 2. Data processed by the application

| Data | Where it is used | Local retention |
| --- | --- | --- |
| Microphone audio | Live coaching conversation and speech processing | Held in application memory during the session; not automatically written to disk |
| Transcript text | Conversation display, optional export, optional coaching review | Held in application memory until discarded or the application closes |
| AI response audio/text | Playback, transcript, optional export | Held in application memory during the session |
| Session metrics | Optional developmental review | Calculated locally from the transcript; sent to the selected provider only when review is requested |
| API key | Authentication to the selected provider | Kept in memory, or stored in Windows Credential Manager/macOS Keychain if the user enables secure key storage |
| Exported Word/MP3 files | User-selected local output | Stored wherever the user chooses; Presence does not encrypt exported files |

Presence does not automatically save a session recording to disk.

## 3. Cloud AI providers

Presence is a bring-your-own-key application. The user selects and authenticates to a provider using their own API credentials.

### Google Gemini

When Gemini is selected, live voice/text and generated responses are processed through Google Gemini.

Google's current Gemini API terms distinguish between unpaid and paid services. Google states that unpaid-service content may be used to improve Google products and may be reviewed by humans, and it instructs users not to submit sensitive, confidential, or personal information to unpaid services. For Paid Services, Google states that prompts and responses are not used to improve its products and are processed under Google's Data Processing Addendum, subject to limited logging for safety, security, and legal/regulatory purposes.

Google's current pricing page lists the standard Free Tier for `gemini-3.8-live` as free of charge for input and output, subject to project/model limits, and marks Free Tier content as used to improve Google products while Paid Tier content is not used for that purpose.

Google's current terms also state that API clients made available to users in the European Economic Area, Switzerland, or the United Kingdom must use Paid Services.

Current pricing and data-use information:  
https://ai.google.dev/gemini-api/docs/pricing

Current terms:  
https://ai.google.dev/gemini-api/terms

Gemini zero-data-retention guidance:  
https://ai.google.dev/gemini-api/docs/zdr

### GroqCloud

When Groq is selected:

1. spoken turns are sent to Groq Whisper for speech-to-text;
2. conversation text is sent to the selected Groq-hosted chat model;
3. generated reply text is sent to Groq Orpheus for speech generation.

Groq currently states that inference customer data is not retained by default except for limited cases such as features that require persistence or temporary system-reliability/abuse-monitoring logs. Groq documents a Zero Data Retention setting and states that retained customer data is stored in the United States, with contractual transfer safeguards where applicable.

Current data information:  
https://console.groq.com/docs/your-data

Groq Data Processing Addendum:  
https://console.groq.com/docs/legal/customer-data-processing-addendum

Provider terms and technical behavior can change. Users should verify the current provider terms and their own account settings before processing real or sensitive information.

## 4. Purpose limitation and data minimisation

Presence processes conversation information only to provide the requested coaching conversation, transcript, export, or optional developmental review.

Users should avoid entering names, identifiers, health information, employment-confidential information, or other sensitive details unless they are genuinely necessary and the user is permitted to process them.

For practice, fictional or de-identified scenarios are preferred.

## 5. Consent and lawful basis

The in-app provider checkbox is an **authorization control**. It confirms that the user permits Presence to send the current session's voice/text to the selected provider.

It is **not** a substitute for the lawful basis required under data-protection law when another person's personal data is processed.

If a real coach, employer, training organization, or other professional uses Presence with another person's information, that user or organization should determine its role and obligations, including:

- the appropriate lawful basis under GDPR Article 6;
- an Article 9 condition if special-category data is processed;
- privacy information that must be provided to the individual;
- whether consent to audio recording is required under applicable local law or contract;
- confidentiality, professional-ethics, employment, and organizational requirements.

The project maintainer does not receive coaching-session content merely because the local application is used.

## 6. Session authorization and withdrawal

Provider authorization is session-scoped in the current application.

- A new provider selection clears the checkbox.
- Completion of a voice session clears the checkbox.
- If the checkbox is withdrawn while a live session is running, Presence ends the live session so no further voice/text is intentionally sent by the application.
- If session authorization is no longer active, generating an AI coaching review asks for a separate explicit confirmation before the visible transcript and metrics are sent to the selected provider.

## 7. Storage, retention, and deletion

### In-memory session data

The user can open **Privacy & data use** and choose **Discard current session data**.

This clears the current in-memory transcript and captured session audio from Presence. Closing the application also ends the local in-memory session.

### Exported files

If the user exports a transcript, developmental review, or MP3 recording, the file is stored in the user-selected location. Presence does not manage the retention of those files and does not encrypt them.

The user is responsible for deleting, securing, or retaining exported files according to their needs and obligations.

### Provider-side data

The local discard action cannot delete information already processed or retained by Google, Groq, or another provider. Provider-side access, deletion, retention, and objection rights must be exercised using that provider's applicable controls and privacy process.

## 8. International transfers

Cloud AI providers may process or retain information outside the user's country.

Google states that Paid Services data may be stored transiently or cached in countries where Google or its agents maintain facilities and provides contractual data-processing terms for eligible services.

Groq states that retained customer data is stored on Google Cloud Platform in the United States and refers to Standard Contractual Clauses where applicable.

Organizations subject to GDPR should assess transfer mechanisms and provider settings for their own use case.

## 9. Individual rights

Depending on the context and applicable law, individuals may have rights including access, correction, erasure, restriction, portability, objection, withdrawal of consent, and complaint to a supervisory authority.

Because Presence does not maintain a central project-operated store of coaching sessions, the project maintainer will normally have no session transcript or recording to retrieve, correct, or erase.

For:

- **local in-memory data:** use the in-app discard control or close the application;
- **exported files:** manage the files directly on the user's device/storage;
- **provider-side data:** use the selected provider's privacy and account controls;
- **organization-managed sessions:** contact the organization or professional who decided to use Presence.

## 10. Security

Current safeguards include:

- local-first session handling;
- no automatic recording file;
- explicit export actions;
- operating-system credential storage for saved API keys;
- no API keys committed to the repository;
- session-scoped provider authorization;
- an explicit in-memory discard control.

No software can guarantee absolute security. Exported Word and MP3 files are not encrypted by Presence.

## 11. Adults only

Presence is intended for users aged **18 or older**.

This also aligns with the current Google Gemini API age requirements for API clients using Gemini.

## 12. Automated decision-making

Presence provides coaching conversation, practice, reflection, metrics, and developmental feedback.

It is not designed to make decisions producing legal or similarly significant effects about employment, hiring, promotion, credentials, health, finance, or other high-impact matters. AI-generated coaching reviews are developmental prompts and require human judgment.

## 13. Real-client and organizational use

Before using real-client information, users should consider:

- whether a fictional/de-identified scenario would be sufficient;
- whether the AI provider and plan are approved by their organization;
- whether a Data Processing Agreement is required;
- whether a Data Protection Impact Assessment is appropriate;
- whether international transfer safeguards are required;
- whether coaching confidentiality and professional-ethics obligations permit the processing;
- how exported files will be encrypted, retained, shared, and deleted.

## 14. Privacy questions

Privacy questions about the open-source project can be directed to the project maintainer using the contact channel shown on the maintainer's GitHub profile:

https://github.com/agilecoach-ashutosh

Do **not** post API keys, transcripts, recordings, client names, or other personal/confidential session information in a public GitHub issue.

For requests concerning provider-held information, contact Google or Groq through their applicable privacy/account channels.

## 15. Changes to this notice

This notice may be updated as Presence changes providers, storage behavior, export behavior, or privacy controls. The Git history provides a versioned record of changes.
