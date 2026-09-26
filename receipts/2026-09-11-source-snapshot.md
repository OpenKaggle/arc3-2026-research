# Source and environment receipt — 2026-09-11

## Collection boundary

- Collected between `2026-09-11T01:05Z` and `2026-09-11T01:12:43Z`.
- Read-only sources: Kaggle live UI/API/pages, ARC Prize official site/docs,
  official `arcprize` GitHub metadata, and local file metadata/safe framework
  source.
- No competition file was downloaded or opened; only the public file listing
  (name, size, timestamp) was queried.
- No Join button, form submission, upload, notebook push, Phase-B rerun, GPU,
  or private-evaluation action occurred.
- No API token, cookie, personal address, birth date, employer identity, or tax
  data is stored in this receipt.

## Kaggle API receipt

At `2026-09-11T01:09:38Z`, `kaggle competitions list` returned:

```text
ref=https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3
deadline=2026-11-02 23:59:00
category=Featured
reward=850,000 Usd
teamCount=2952
userHasEntered=False
```

The logged-in browser independently displayed `Join Competition`. It was not
clicked.

The live public leaderboard top three at the snapshot were:

```text
Tufa Labs          11.04
Third Intelligence  8.21
Daniel Franzen      7.63
```

## Exact Kaggle page excerpts

Timeline:

```text
June 30, 2026 (optional) - Deadline for Milestone 1.
September 30, 2026 (optional) - Deadline for Milestone 2.
October 26, 2026 - Entry Deadline.
October 26, 2026 - Team Merger Deadline.
November 2, 2026 - Final Submission Deadline.
All deadlines are at 11:59 PM UTC ...
```

Specific Rules:

```text
The maximum Team size is eight (8).
You may submit a maximum of 1 (1) Submissions per day.
You may select up to two (2) Final Submissions for judging.
```

Code Requirements:

```text
CPU Notebook <= 9 hours run-time
GPU Notebook <= 9 hours run-time
Internet access disabled
Freely & publicly available external data is allowed, including pre-trained models
Submission file will be automatically generated.
```

License and delivery:

```text
WINNER LICENSE TYPE: CC-BY 4.0
DATA ACCESS AND USE: Apache 2.0
Submissions are required to have open source system, open source model,
and open source weights/parameters ...
```

## Official repository heads

```text
ARC-AGI                         f12822c4d550121c35a275008d964afbbed47d2f
ARC-AGI-3-Agents                4743e7d0aaae0ded0d98a89a7e282e63564cd58b
ARC-AGI-3-Kaggle-Starter        eeb1535404f321d280a8f9194bbc1d7aca5f05fc
arc-agi-3-benchmarking          eb6b8cd5ca8ad001339bb0184fdb979e93031679
```

GitHub's repository API reported MIT for the toolkit, agent framework, and
benchmarking repository. It reported no detected license for the Starter; that
repository remains reference-only.

The Kaggle public file listing identified 25 public environment directories
and a bundle containing `arc_agi-0.9.8` and `arcengine-0.9.3`. Contents and
hashes were not acquired because Entry is blocked.

## Local environment

```text
host architecture: arm64
Python 3.12.3: available
Python 3.13.2: workspace default
uv 0.5.11: available
arc_agi in Python 3.12: not installed
filesystem: 926 GiB total, about 58 GiB available, 94% used
arc2_paper: about 8.9 GiB, 2,536 files
```

The new baseline must therefore create a Python 3.12 lock from scratch and
must not inherit the workspace `.venv`.

## Source URLs

See the complete first-party URL list in `docs/RULES_AUDIT.md`. The current
receipt must be refreshed immediately before Entry, Milestone publication,
team merge, Phase-B submission, and final-submission selection because Kaggle
explicitly reserves the right to change the timeline.
