# ARC-AGI-3 rules and deadline audit

Snapshot: `2026-09-11T01:12:43Z`. Sources are limited to Kaggle, ARC Prize
Foundation, its official documentation, and the official `arcprize` GitHub
organization. This is an operational audit, not legal advice.

## Operative deadlines

Kaggle's live Timeline states that all listed deadlines are `11:59 PM UTC`
unless otherwise noted.

| Event | UTC | Asia/Shanghai | Audit state |
|---|---:|---:|---|
| Start | 2026-03-25 | — | passed |
| Milestone 1 (optional) | 2026-06-30 23:59 | 2026-07-01 07:59 | passed |
| Milestone 2 (optional) | 2026-09-30 23:59 | 2026-10-01 07:59 | open |
| Entry | 2026-10-26 23:59 | 2026-10-27 07:59 | rules must be accepted before this |
| Team merger | 2026-10-26 23:59 | 2026-10-27 07:59 | merge/join team before this |
| Final submission | 2026-11-02 23:59 | 2026-11-03 07:59 | binding Kaggle deadline |
| Winners announced | 2026-12-04 | not specified | informational |

The page header's local close time, `2026-11-03 07:59` in China Standard
Time, is the timezone conversion of the Kaggle final deadline and is **not** a
conflict.

## Binding operational constraints

| Area | Current Kaggle rule/page |
|---|---|
| Eligibility | Registered Kaggle account; at least the higher of 18 or local age of majority; excluded territories and U.S. sanctions restrictions apply; local law also applies. |
| Employer/entity | If acting for or within the scope of an employer/entity, it must know and consent, including to possible prize receipt, and internal policy must allow it. |
| Competition entities | Their employees/interns/contractors/officers/directors may participate subject to policy but cannot win prizes. |
| Accounts/teams | One unique Kaggle account; one team; maximum team size 8; merger submission totals must remain within the then-applicable allowance. |
| Submission | Maximum 1 formal submission per day; up to 2 final submissions. |
| Format/runtime | Notebook only; CPU or GPU notebook at most 9 hours; internet disabled; output is generated automatically. |
| External assets | External data/models/tools must be free and equally publicly accessible, or meet the Host's reasonable-access/minimal-cost test; all licenses must permit compliance. |
| Human labeling | Validation/test hand-labeling or human prediction is prohibited except where a Hackathon expressly allows it. This track is not treated as such an exception. |
| Data security | Competition data may be used commercially or non-commercially, but must not be provided to people who have not accepted the Rules. |
| Code sharing | No private sharing of competition code/data outside a team. Public competition code must be shared for all competitors through the competition's Kaggle forum/notebooks and under a commercially usable OSI-approved license. |
| Winner license | Kaggle identifies `CC BY 4.0`; the text also requires open-source system, model, and weights/parameters and links the OSI Open Source AI checklist. |
| Winner delivery | Reproducible training and inference code, environment/resources, detailed method, license rights, sponsor documentation/interview, award documents, and tax forms may be required. |
| Taxes/publicity/privacy | Winner bears taxes; name/likeness may be used; account/competition personal data may be transferred to the U.S.-based Sponsor. |

The Rules contain tension between requiring an open-source model/weights and
also saying that input data or pretrained models with an incompatible license
need not be relicensed. Until the Sponsor resolves that text, this campaign
allows only assets that are public, reproducible, commercially usable, and
compatible with the OSI checklist.

## Official-source conflicts

These are not silently reconciled:

| Topic | Kaggle | Other official source | Conservative control |
|---|---|---|---|
| Daily submissions | Rules: 1/day | Official Starter README at commit `eeb1535...`: 5/day | Enforce 1/day. |
| Milestone split | `$25k / $7.5k / $5k` | ARC track: `$25k / $10k / $2.5k` | Treat payout as unresolved; do not budget against it. |
| $700k prize | End-of-competition top five 100% teams split `$350k/$175k/$70k/$70k/$35k` | ARC track: first eligible 100% agent receives it; otherwise rolls over | Treat mechanism as unresolved; request written Sponsor clarification before a prize-dependent decision. |
| Original-work license | Winner submission/source: CC BY 4.0 | ARC 2026 overview: submitter-authored code/methods under CC0 or MIT-0 | Use permissive OSI code license plus an explicit CC BY 4.0 grant if authorized; obtain written confirmation before prize claim. |
| Per-level score | Kaggle Evaluation text still describes a 100% cap | Current ARC methodology and official toolkit changelog: cap `1.15`, upper-median human baseline | Implement current official engine; never reimplement scoring from stale prose. |
| Paper deadline | Kaggle Paper Track: 2026-11-09 23:59 UTC | ARC 2026 overview: November 8 | Use November 8 as internal latest date and verify Kaggle live page before submission. |
| Scorecard auto-close | Docs pages contain 15-minute and 24-hour statements | — | Close explicitly; do not depend on auto-close. |

The Kaggle Rules define the Kaggle competition URL as the Competition Website,
so Kaggle's live Rules/Timeline are the primary entry and submission controls.
Where two official sources conflict and neither clearly controls, use the
earlier/stricter constraint and obtain written Sponsor clarification.

## Award and Paper Track implications

- Milestone eligibility requires the notebook to be public under an
  open-source license by the milestone deadline.
- The Paper Track is a separate entry and submission. It requires a submitted
  Kaggle Writeup, Media Gallery, cover, attached public notebook, and a real
  ARC-AGI-2 or ARC-AGI-3 submission ID. Drafts do not count.
- The Paper team must match the corresponding ARC team; maximum size is 8 and
  one Paper submission is allowed per team.
- A private Kaggle resource attached to the public Writeup may become public
  automatically after the deadline.
- The evaluation has six equally weighted criteria: Accuracy, Universality,
  Progress, Theory, Completeness, and Novelty. The Writeup guidance is 1,500
  words. Main awards are `$50k/$20k/$5k`; papers over `4.5/5` may share a
  conditional `$375k` pool.

## Baseline-relevant facts

- Frames contain a grid no larger than `64x64`, cell values `0..15`, metadata,
  state, and currently available actions; one action can return multiple
  frames.
- Actions are `RESET`, `ACTION1..ACTION7`; `ACTION6` needs `(x,y)` in
  `0..63`. Meanings vary by game, so direction semantics must not be assumed.
- Current methodology computes completed-level score as
  `(human_baseline_actions / agent_actions)^2`, capped at `1.15`, weights later
  levels by their 1-based index, and averages game scores. Internal reasoning
  that does not affect the environment does not count as an action.
- Kaggle's data page currently describes 25 public games and a separate 110-game
  private evaluation split approximately half for public and private
  leaderboards. The count is evidence, not a value the agent should hardcode.
- The Kaggle file snapshot bundles `arc_agi==0.9.8` and
  `arcengine==0.9.3`. Parity testing must use the bundle actually attached to
  the competition, not assume the current repository head is equivalent.
- The only confirmed overall competition wall-clock is 9 hours. Per-game
  action, reset, token, RAM, VRAM, and wall-time limits are not frozen by the
  audited Rules and must remain configurable/fail-closed.

## Status at snapshot

- Kaggle API: `userHasEntered=False`, deadline `2026-11-02 23:59:00`,
  reward `$850,000`, `2,952` teams.
- Browser: visible `Join Competition` button; it was not clicked.
- Public leaderboard top 3: `11.04`, `8.21`, `7.63`.
- No Join, download, upload, notebook commit, submission, or accelerator use
  occurred.

## First-party sources

- Kaggle Rules: <https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/rules>
- Kaggle Timeline: <https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview/timeline>
- Kaggle Overview/Code Requirements/Prizes/Data:
  <https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/overview>
- Kaggle Paper Track:
  <https://www.kaggle.com/competitions/arc-prize-2026-paper-track/overview>
- ARC Prize 2026 overview: <https://arcprize.org/competitions/2026>
- ARC-AGI-3 track: <https://arcprize.org/competitions/2026/arc-agi-3>
- ARC scoring methodology: <https://docs.arcprize.org/methodology>
- ARC testing policy: <https://arcprize.org/policy>
- Official toolkit: <https://github.com/arcprize/ARC-AGI>
- Official agent framework: <https://github.com/arcprize/ARC-AGI-3-Agents>
- Official Kaggle starter:
  <https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter>
