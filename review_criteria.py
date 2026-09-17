"""Level-specific developmental review criteria for Presence Coach.

ACC and PCC criteria below are grounded in the user-selected ICF reference documents:
- ACC Behaviorally Anchored Rating Scales (BARS), August 2022.
- ICF PCC Markers, revised November 2020 / rev. 06.25.21.

MCC criteria are a concise paraphrase of the ICF MCC Minimum Skills Requirements,
rev. January 26, 2026. These criteria are used only for developmental AI review and
must never be presented as an official ICF assessment, score, or pass/fail decision.
"""
from __future__ import annotations


ACC_SOURCE = "ICF ACC Behaviorally Anchored Rating Scales (BARS), August 2022"
PCC_SOURCE = "ICF Professional Certified Coach (PCC) Markers, rev. 06.25.21"
MCC_SOURCE = "ICF MCC Minimum Skills Requirements, rev. January 26, 2026"


ACC_CRITERIA = """
SOURCE: ICF ACC Behaviorally Anchored Rating Scales (BARS), August 2022.
Use these behavioral statements as developmental evidence anchors, not as a formulaic
checklist or an official pass/fail assessment.

Competency 1 — Demonstrates Ethical Practice
- Qualifier E1: Coach demonstrates alignment with the ICF Code of Ethics.
- Qualifier E2: Coach demonstrates consistent alignment with the role of coach.
For transcript-only review, report only observable role/ethics evidence. Do not infer
private conduct, contracting, confidentiality practices, or circumstances not shown.

Competency 2 — Embodies a Coaching Mindset
- The ACC BARS document has no session behavioral statements for this competency.
- Do not score this competency from one transcript. You may note transcript evidence
  relevant to curiosity/flexibility, but label it as limited and non-diagnostic.

Competency 3 — Establishes and Maintains Agreements
- A3.1 Coach invites the client to identify their desired coaching outcome.
- A3.2 Coach and client reach an agreement on what the client wants to accomplish in the session.
- A3.3 Coach shows curiosity about the client and how the client relates to what they want to accomplish.
- A3.4 Coach attends to the agenda set by the client throughout the session unless the client indicates otherwise.

Competency 4 — Cultivates Trust and Safety
- A4.1 Coach acknowledges client insights and learning in the moment.
- A4.2 Coach explores the client's expression of feelings, perceptions, concerns, beliefs, or suggestions.
- A4.3 Coach expresses support and concern for the client, which may focus on the client's context, problem, or situation rather than the client holistically.

Competency 5 — Maintains Presence
- A5.1 Coach is curious throughout the session.
- A5.2 Coach acknowledges situations that the client presents.
- A5.3 Coach allows the client to direct the conversation at least some of the time.

Competency 6 — Listens Actively
- A6.1 Coach uses summarizing or paraphrasing to make sure they understood the client correctly.
- A6.2 Coach makes observations that support the client in creating new associations.
- A6.3 Coach co-creates a shared vision with the client.

Competency 7 — Evokes Awareness
- A7.1 Coach acknowledges the client's new awareness, learning, and movement toward the desired outcome.
- A7.2 Coach supports the client in viewing the situation from new or different perspectives.
- A7.3 Coach inquires about or explores the client's ideas, beliefs, thinking, emotions, and behaviors in relation to the desired outcome.

Competency 8 — Facilitates Client Growth
- A8.1 Coach partners with the client to create or confirm specific action plans.
- A8.2 Coach asks questions to support the client in translating awareness into action.
- A8.3 Coach supports the client to close the session.
"""


PCC_CRITERIA = """
SOURCE: ICF Professional Certified Coach (PCC) Markers, rev. 06.25.21.
Use these markers as developmental evidence anchors, not as a formulaic checklist or
an official pass/fail assessment.

Competency 1 — Demonstrates Ethical Practice
- Look for observable alignment with the ICF Code of Ethics and consistency in the role of coach.

Competency 2 — Embodies a Coaching Mindset
- The PCC document notes that some aspects may be visible through markers 4.1, 4.3, 4.4,
  5.1, 5.2, 5.3, 5.4, 6.1, 6.5, 7.1, and 7.5, while the competency itself extends beyond
  what one recorded conversation can demonstrate.

Competency 3 — Establishes and Maintains Agreements
- 3.1 Coach partners with the client to identify or reconfirm what the client wants to accomplish in this session.
- 3.2 Coach partners with the client to define or reconfirm measures of success for what the client wants to accomplish.
- 3.3 Coach explores what is important or meaningful to the client about what they want to accomplish.
- 3.4 Coach partners with the client to define what the client believes they need to address to achieve the desired session outcome.

Competency 4 — Cultivates Trust and Safety
- 4.1 Coach acknowledges and respects the client's unique talents, insights, and work in the coaching process.
- 4.2 Coach shows support, empathy, or concern for the client.
- 4.3 Coach acknowledges and supports the client's expression of feelings, perceptions, concerns, beliefs, or suggestions.
- 4.4 Coach invites the client to respond in any way to the coach's contributions and accepts the client's response.

Competency 5 — Maintains Presence
- 5.1 Coach responds to the whole person of the client (the who).
- 5.2 Coach responds to what the client wants to accomplish throughout the session (the what).
- 5.3 Coach supports the client to choose what happens in the session.
- 5.4 Coach demonstrates curiosity to learn more about the client.
- 5.5 Coach allows for silence, pause, or reflection.

Competency 6 — Listens Actively
- 6.1 Questions and observations are customized using what the coach has learned about who the client is or the client's situation.
- 6.2 Coach explores the words the client uses.
- 6.3 Coach explores the client's emotions.
- 6.4 Coach explores energy shifts, nonverbal cues, or other behaviors.
- 6.5 Coach explores how the client currently perceives themself or their world.
- 6.6 Coach allows the client to complete speaking without interrupting unless there is a stated coaching purpose.
- 6.7 Coach succinctly reflects or summarizes what the client communicated to support clarity and understanding.

Competency 7 — Evokes Awareness
- 7.1 Coach asks about the client: thinking, feeling, values, needs, wants, beliefs, or behavior.
- 7.2 Coach helps the client explore beyond current thinking/feeling to expanded ways of thinking/feeling about themself (the who).
- 7.3 Coach helps the client explore beyond current thinking/feeling to expanded ways of thinking/feeling about the situation (the what).
- 7.4 Coach helps the client explore beyond current thinking, feeling, or behaving toward the desired outcome.
- 7.5 Coach shares observations, intuitions, comments, thoughts, or feelings without attachment and invites the client's exploration.
- 7.6 Coach asks clear, direct, primarily open-ended questions, one at a time, at a pace allowing reflection.
- 7.7 Coach uses generally clear and concise language.
- 7.8 Coach allows the client to do most of the talking.

Competency 8 — Facilitates Client Growth
- 8.1 Coach invites or allows the client to explore progress toward the desired session outcome.
- 8.2 Coach invites the client to state or explore learning about themself (the who).
- 8.3 Coach invites the client to state or explore learning about the situation (the what).
- 8.4 Coach invites the client to consider how they will use new learning from the session.
- 8.5 Coach partners with the client to design post-session thinking, reflection, or action.
- 8.6 Coach partners with the client to consider how to move forward, including resources, support, or potential barriers.
- 8.7 Coach partners with the client to design the best methods of accountability for themself.
- 8.8 Coach celebrates the client's progress and learning.
- 8.9 Coach partners with the client on how they want to complete the session.

TRANSCRIPT LIMITATION
Marker 6.4 cannot be reliably evaluated from a text transcript alone unless an explicit
session note captures the relevant observable cue. Silence/pause (5.5), interruption
quality (6.6), tone, energy, and other audio/nonverbal behaviors may also be only
partially assessable from transcript and local metrics. Mark these Not assessable or
Limited evidence rather than inventing evidence.
"""


MCC_CRITERIA = """
SOURCE: ICF MCC Minimum Skills Requirements, rev. January 26, 2026.
This is a concise developmental paraphrase of the official MCC behavioral standard.
Use it as a holistic mastery lens, not a checklist or official pass/fail assessment.

Competency 1 — Demonstrates Ethical Practice
Consistent evidence: stays clearly in the coaching role; uses trust, presence, listening,
and awareness-evoking skills to facilitate the client's own insight; avoids advice-led,
consulting-led, or therapeutic-mode conversation.
Watch for: telling the client what to do, centering the coach's expertise, or moving
outside the coaching role.

Competency 2 — Embodies a Coaching Mindset
The official MCC MSR says this competency develops across the coach's professional
journey and is evaluated through credentialing knowledge assessment. Do not score it
from one transcript; at most note limited session evidence of openness, curiosity,
flexibility, and client-centeredness.

Competency 3 — Establishes and Maintains Agreements
Consistent evidence: co-creates the session focus; explores enough dimensions of the
topic to clarify intent; confirms shared understanding of the desired outcome; notices
emerging shifts and re-contracts direction with the client when needed.
Watch for: vague or coach-led agreements, generic responses, missing shifts, or subtly
influencing how the client should use the session.

Competency 4 — Cultivates Trust and Safety
Consistent evidence: recognizes learning/growth as it appears; notices and respects the
client's emotions, strengths, identity, perspectives, and unique way of processing;
demonstrates empathy and genuine curiosity about the person.
Watch for: prioritizing the coach's interpretation, generic responses, judgment,
dismissiveness, or missed opportunities to acknowledge the client's contributions.

Competency 5 — Maintains Presence
Consistent evidence: responds to the whole person in real time; partners around the
client's needs; remains consistently curious; creates genuine space for reflection,
pause, and silence.
Watch for: predefined technique use, teaching/influencing, treating the client as less
than an equal partner, focusing only on the situation, or crowding the client's space.

Competency 6 — Listens Actively
Consistent evidence: hears nuance in language, emotion, energy, and behavior in relation
to the client's agenda; responds to the client's thinking/feeling/insight in the moment;
explores multiple dimensions of the client rather than only solving the situation.
Watch for: generic questions, solution focus, coach-knowledge focus, or missed client
language/meaning. Audio/nonverbal elements must be marked Not assessable when absent.

Competency 7 — Evokes Awareness
Consistent evidence: partners to expand perspective; offers observations or intuitions
without attachment when useful; uses succinct open questions one at a time; allows
sufficient reflective space for emerging awareness about both the person and topic.
Watch for: driving solutions, complex/confusing coach language, insufficient space,
ignoring the client's words/creative style, or overusing questions instead of other
awareness-evoking approaches.

Competency 8 — Facilitates Client Growth
Consistent evidence: invites learning about the self; partners to integrate learning
into meaningful action when the client wants action; supports client-owned follow-through;
and partners on how/when to complete the session.
Watch for: coach-prescribed actions, weak integration of learning, missed learning or
progress, underdeveloped implementation, or coach-controlled closure.

TRANSCRIPT LIMITATION
MCC mastery includes nuance, silence, energy, behavior, and nonverbal responsiveness.
A text transcript cannot fully evidence these. Mark such areas Not assessable or
Limited evidence rather than inferring tone, body language, or energy.
"""


def get_review_criteria(level: str) -> tuple[str, str]:
    level = (level or "PCC").upper()
    if level == "ACC":
        return ACC_SOURCE, ACC_CRITERIA
    if level == "MCC":
        return MCC_SOURCE, MCC_CRITERIA
    return PCC_SOURCE, PCC_CRITERIA
