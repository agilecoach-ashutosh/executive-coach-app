# Agile Orbit integration into Presence Coach

The source of truth for this review is the repository revision recorded in
`agile-orbit-source-manifest.json`. The rendered website could not be loaded by
the web reader, so HTML and JavaScript were inspected directly. This is a snapshot,
not automatic website syncing, model fine-tuning, or a guarantee of live behaviour.

## What enters each live session

`coaching.py` supplies the original core prompt plus distilled Agile Orbit practice
and all 23 question-function purposes/watch-outs. `engine.py` already sends the
combined `SYSTEM_PROMPT` as the Gemini Live system instruction. No new dependency,
file-loading step, or installer asset is required. Full question examples are kept
in the adjacent JSON for review, not injected as a script into every session.

| Website content | Application behaviour |
| --- | --- |
| Fundamentals, mindset, Empty Cup | Process belongs to coach; meaning and choices belong to client; reset assumptions. |
| Coachee basics, preparation, topics, journey | Uncertainty and unfinished goals are welcome; do not mandate action or continued sessions. |
| Listening and question lab | Exact language, one inquiry, attention to context; do not infer hidden truths. |
| Session agreement and session lab | Separate topic from desired usefulness; re-contract on changes; recognise advice traps. |
| Metaphor and DOQ | Preserve client imagery; consider conversational direction without forcing positivity. |
| Models and theories | Light, optional scaffolding; do not diagnose, teach, or force an acronym. |
| Reflection tools | Permission first, client-provided content; scores never determine priorities or decisions. |
| Chemistry, agreements, ethics | Role clarity, actual capabilities/data handling, client choice and professional scope. |
| Impact and closure | Client-defined learning; no fabricated outcomes, ROI or causal attribution. |
| Team/stakeholder models | Context lenses only; no invented feedback or simulated consent of absent people. |
| Reading guide | Source summaries inform reflective inquiry; not a claim to have read the books. |

## Deliberate adaptations and source limits

- The website permits explicit changes of professional role. The owner's newer app
  instruction is stricter: **remain in coaching mode and do not generate solutions**.
  That instruction wins, including after a request to brainstorm.
- Some site examples contain several questions or presume a goal, feeling or
  possible direction. They are not copied verbatim into runtime turns. Use one
  relevant inquiry, remove assumptions and avoid prescribing a new option.
- Body-language guidance is adapted to audio/text. This app has no camera access.
- Browser tools and scores are not integrated into the desktop app. The model can
  facilitate a consensual verbal reflection, not claim to operate a canvas.
- The legacy tools JavaScript still includes labels such as 'Wheel of Life 2.0'
  and a Values tab. Those UI details are not imported. Source and deployed UI may
  differ; this task changes only executive-coach-app.
- Transformative learning is only named in the site's source handout summary;
  no missing teaching is invented or attributed to the owner.
- Links to AI-augmented coaching, ICF reflection and coaching journal have no matching
  files at those paths in the checked revision. Their contents were not invented.
- No full external books, restricted handout questions, proprietary diagrams, or
  linked external training courses were ingested. The 184 preserved questions are
  the website's explicitly original Agile Orbit questions.

## Validation

Transport/turn-taking tests are independent of coaching quality. The actual model
must be evaluated with the scenarios in `COACHING-REVIEW.md`. A stronger prompt is
not an output filter; it can still fail. Reviewer feedback should improve this
versioned prompt rather than being presented as an ICF assessment or training claim.
