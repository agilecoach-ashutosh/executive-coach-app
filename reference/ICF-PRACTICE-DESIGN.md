# Empathy and professional coaching practice

Reviewed 2026-09-17. This is an original product design adaptation, not an ICF
assessment instrument, endorsement, or claim that Presence holds a credential.

## Official sources

- [2025 ICF Core Competencies](https://coachingfederation.org/credentialing/coaching-competencies/icf-core-competencies/): relationship, ethics, listening, and client growth frame the design.
- [PCC Minimum Skills Requirements](https://coachingfederation.org/wp-content/uploads/2025/09/icf-cs-pcc-minimum-skills-requirements.pdf), PDF revision 1.26.2026: informed agreement, individualised listening, and acceptance of the client's response.
- [MCC Minimum Skills Requirements](https://coachingfederation.org/wp-content/uploads/2025/09/icf-cs-mcc-minimum-skills-requirements.pdf), PDF revision 1.26.2026: informed responsive presence, empathy, and space for the client's own exploration.

The resource landing pages show older dates; the PDF revision dates above are the
versions actually consulted. Recheck official sources when changing this design.

## Implementation choices

`coaching.py` supplies Gemini's system instruction. The new rules explicitly handle
emotionally significant openings, correction of emotional labels, requests for fewer
questions, permission before a sensitive observation, and insights that need time.
They retain the owner's strict rule against coach-generated solutions, including
when asked to brainstorm. This is a product choice, not a claim that every human
coaching engagement must use identical boundaries.

The application translates these intentions into prompt guidance, not deterministic
response enforcement. Examples and review cases are original hypothetical scenarios.
The model may still lead, miss nuance, or use formulaic empathy. It has no video,
human felt experience, or dependable cross-session memory. Silence still depends
on the existing audio turn gate and the client's controls; prompt changes do not
change those mechanics. No hidden emotion classifier or credential-level selector
has been added.

Review `COACHING-REVIEW.md` for comparison sessions and observable failure signals.
Only live testing and qualified human review can provide evidence about the quality
of these behaviours; passing Python tests cannot establish PCC/MCC equivalence.
