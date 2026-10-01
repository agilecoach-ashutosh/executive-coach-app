# AI coach presence: source comparison and validation

This is an experimental coach-instruction change, not a claim of PCC/MCC equivalence.
Source review: 1 October 2026. Public demonstrations are learning references, not
proof that every intervention is appropriate for this app.

## Sources inspected

- Sunita Chhibar (PCC), with commentary from Merci Miglino (MCC):
  https://icacoach.com/articles/sunita-chhibar-coaching-demo/
  Public dialogue and annotated-transcript link. The coach notices the change from
  wanting practical structures to wanting clarity, then checks that change with
  the client. This informs following emerging meaning, not forcing the initial agenda.
- Poyee Poon Dorian (PCC), with commentary from Merci Miglino (MCC):
  https://icacoach.com/articles/poyee-poon-dorian/
  Public dialogue and annotated-transcript link. Client language and metaphor
  recur across the conversation. An exercise is offered as an invitation.
  The transferable pattern is client-specific continuity and permission, not
  reproducing visual observations or that coach's particular somatic technique.
- Claude Arribas: annotated French transcript described by the author as one of
  the recordings accepted for his MCC credential:
  https://www.anse.fr/francais/script-de-la-seance-de-coaching-pour-l-obtention-de-mon-mcc/
  https://www.anse.fr/webmanager/contentimages/subcnt8379.pdf
  Inspected the dialogue and coach/client commentary around agreement, silence
  and an observation the client did not pursue. The coach describes releasing
  that interpretation. Credential-pass status is the author's account, not an
  independently obtained ICF assessment.
- Current ICF MCC Minimum Skills Requirements:
  https://coachingfederation.org/wp-content/uploads/2025/09/icf-cs-mcc-minimum-skills-requirements.pdf

The ICA demonstrations are older sessions using the earlier competency framework.
Current requirements govern validation. We do not adopt every line of a demonstration:
absolute confidentiality promises, video observations, compulsory exercises and
claims of a human coach's feelings do not fit this app.

No third-party transcript is copied into the app or used to train a model.
Prompt examples are original fictional exchanges. An indexed PDF explicitly
restricted to a private mentor group was excluded. Lyssa deHart's MCC demo
collection advertises recordings, transcripts and client debriefs, but its lesson
contents require an account and were not analysed:
https://academy.lyssadehart.com/course/youtube-mcc-demos

## Change

The previous runtime coach instructions contain about 2,900 whitespace-delimited
words, including a broad framework/tool/question catalogue. The draft replaces
them with about 1,070 words prioritising client-specific listening, response variety,
evolving agreements, accurate within-session continuity, silence, correction repair
and client-owned learning. Five original examples illustrate different response
choices; they are not a script or required sequence.

Deterministic crisis detection, turn gating, simulated-client prompts, review criteria
and audio transport are unchanged. Concision is a hypothesis to test, not evidence
that the voice model will coach better.

## Manual comparison before merge

Compare the baseline and draft using the same provider/model, voice, microphone,
timing settings and comparable scenarios. Vary order across several sessions.
Have a human coach assess recordings as well as transcripts. Keep notes private
unless the client authorises sharing. No API key is needed for repository unit tests;
live comparison requires the user's configured provider.

| Probe (original, fictional) | Behaviour to inspect | Failure indicator |
| --- | --- | --- |
| Client wants a plan, then says understanding a conflict matters more. | Check the emerging direction once and follow the client's choice. | Continue planning automatically or restart all agreement questions. |
| Client uses an unusual metaphor, then abandons it. | Follow their meaning without inventing symbolism; release the metaphor when they move on. | Impose an interpretation or keep bringing the metaphor back. |
| Client says the coach misunderstood an emotion. | Accept the correction and respond to the corrected words. | Defend the interpretation or ask the same rejected question again. |
| Client shares a new insight without asking for action. | Let it settle; acknowledgement or space may suffice. | Praise mechanically and immediately demand a commitment. |
| Client asks for advice or supplies two possible options. | Preserve ownership without adding or ranking options. | Give a solution, imply the best option, or become evasive. |
| Client pauses, resumes quietly, or speaks over the AI. | Check what reaches the provider and whether space feels natural. | Missed words, premature responses or unheard corrections. This may require a separate audio change. |

Ask the client to rate feeling understood, control of direction, thinking space and
useful awareness on a 1-5 scale, with timestamps for specific failures. These are
product-feedback measures, not ICF scores. Also inspect repetition, unsupported
interpretations, leading questions, speech loss and latency. A passing automated
suite verifies regressions, not coaching quality.

A separate reviewer call after every spoken turn is not part of this draft.
It would introduce latency and needs its own evaluation.
