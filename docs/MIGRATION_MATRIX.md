# ARC-AGI-2 / Paper asset migration audit

Snapshot: `2026-09-11T09:11:07+0800`.

## Decision

Only evidence-system **designs** may migrate. Existing ARC-2 solvers, rules,
weights, datasets, candidate notebooks, outputs, scores, and experiment history
are excluded from the ARC-3 baseline.

The workspace root and `arc2_paper/` are not Git repositories, so they do not
provide a trustworthy clean-history boundary. The only clean checkout found is
the official ARC-AGI-2 repository at commit
`f3283f727488ad98fe575ea6a5ac981e4a188e49`; its task data still remains out of
scope for ARC-3.

The legacy pipeline explicitly records
`CONTAMINATED_FOR_V176_GENERALIZATION` and `promotion_blocked=true`; an earlier
audit loaded all 1,000 ARC-AGI-2 training solutions. Re-splitting that corpus
cannot restore an unseen holdout.

## Hard denylist

The ARC-3 runner must not copy, mount, symlink, import, scan for features, or
add these paths to `PYTHONPATH`:

```text
../arc2_paper/official/competition_files
../arc2_paper/evaluator_only
../arc2_paper/artifacts
../arc2_paper/kaggle_runs
../arc2_paper/candidate_notebooks
../arc2_paper/public_notebooks
../arc2_paper/paper/results
../arc2_paper/public_assets
../arc2_paper/experiment_log.csv
../arc2_paper/paper/07_evidence_registry.md
```

This also excludes all ARC-2 solver, selector, fold-building, analysis, and
submission scripts. In particular, the `6.8 GiB` Qwen asset, `2.0 GiB` TRM
checkpoint, the `664,269`-byte `merge_agreement.py`, exact overlays, typed
object rules, and NeuroGolf-derived rules do not enter the first 72 hours.

## Clean-room design references

The following old assets have useful *ideas*, but their code must not be copied
until authorship and license scope are confirmed. ARC-3 versions should be
rewritten from the requirements below and tested only with synthetic fixtures.

| Legacy design | Reusable requirement | Required ARC-3 rewrite |
|---|---|---|
| Release-manifest audit | Exact allowlist; byte count/hash; reject path escape, symlink, secret, absolute path, answer-like files, notebook outputs | New schema and denylist; no ARC-2 paths or assumptions |
| Notebook dependency audit | Bind metadata, dependency, public-access, license, and source receipts | Bind Kaggle ARC-3 runtime and bundled wheel versions |
| Stage authorization | Pre-state hash; one named action; frozen artifact; reject stale/future/multi-run authorization | Stages become identity → acquire → authoring → sealed → phase-A → submit |
| Success/failure receipts | Atomic state transition; preserve failed candidate; ordered diagnostics | Add interactive protocol, frame/action-chain and budget fields |
| Validation protocol | Freeze policy, split, seeds, budgets, stop rules before score | Split by game, never by level/frame; aggregate sealed reporting only |
| License audit | Direct vs declared vs missing evidence; fail closed | Apply ARC-3 OSI/Open Source AI and dual-license ambiguity |

## Snapshot hashes

These hashes identify the inspected legacy bytes; they are **not** an
authorization or license to copy them.

| Item | Files | Bytes | SHA-256 |
|---|---:|---:|---|
| `paper/tools` tree summary | 21 | 333,538 | `34fef42b0ea0adab5dc247171a320b7b9f03e892f56e28c3b86c61bb6e858e2d` |
| `paper/tests` tree summary | 27 | 163,057 | `a06a026eec9ed4f574e43826c02b0219d391ea191eed779147750d53104ffe53` |
| `paper/schemas` tree summary | 5 | 29,554 | `88f00cd10f56f61894cc23074cf281dd7af49123327233779439392b4397cf72` |
| Safe-framework 18-file composite | 18 | — | `c23aac8e3c72a5f4896f03377b9ec1892376472df85826badb59fe4fe3c1663e` |
| `audit_release_manifest.py` | 1 | — | `1a70e6accd06d7824dca15c2c7dfd4f52d0b0d58c41702c2b5a11f9eaf1cbe44` |
| `audit_notebook_dependencies.py` | 1 | — | `b7ea6804e74dcb60622044763894b7d4d5b089c091f1a493630692ba6f59298d` |
| `authorize_stage.py` | 1 | — | `9ba09d4c7ffb3a647105e9897727026ac4938c8461f3903fc471d442a6ff29d0` |
| `commit_stage_receipt.py` | 1 | — | `a1d350ce871ad5d5439777ceac0c6570edfbfe7d934e54fe1f5da959c4be4ee4` |
| `commit_stage_failure_receipt.py` | 1 | — | `dc453dc53227aca8ff46819ab7b8c5ae77af6709ee95a6025b7f3e66af247771` |
| `03_validation_protocol.md` | 1 | — | `ad1d295daf3048766b60d5adb3a7f34c0fec94eb7ea911ca10366f7e4c71e921` |
| `14_license_and_public_risk_audit.md` | 1 | — | `de2c53e4e5541ab667aa335575e0cb3366a4f75a11389e270e488d685e6c708e` |

The old project has no project-level lockfile or complete requirements. Its
offline wheelhouse covers only a subset of the TRM runtime, while the source
requirements include unpinned heavy dependencies. The existing `.venv`, old
Kaggle image digest, Qwen/TRM receipts, and license declarations therefore do
not establish an ARC-3-reproducible environment.

## Future migration gate

Any later proposed asset must independently pass all of these checks:

1. It is useful to ARC-3 without using ARC-2 answers, outputs, task-specific
   rules, learned thresholds, or evaluation feedback.
2. Exact source/version/hash and current public accessibility are frozen.
3. Training data provenance is checked for ARC-3 evaluation contamination.
4. License permits public, commercial-use-compatible release and the required
   winner obligations.
5. Author/employer IP authority is attested.
6. A single-variable, pre-registered synthetic/public ablation beats the clean
   implementation; otherwise the asset stays excluded.
