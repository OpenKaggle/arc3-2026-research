# Identity, authority, and rights gate

This gate cannot be completed from account name, timezone, browser state, or
workspace contents. The account holder must provide truthful facts. A birth
date, street address, tax identifier, employer name, or other unnecessary
sensitive detail is **not** requested.

## Required attestation

Reply with answers to all items below:

1. **Age and jurisdiction:** state the country/region of residence (and
   state/province only if its age of majority differs) and confirm that you are
   at least the higher of 18 or the local age of majority.
2. **Excluded residence:** confirm that you are not resident in Crimea, the
   so-called DNR or LNR, Cuba, Iran, or North Korea.
3. **Sanctions/export controls:** confirm that neither you nor an entity you
   represent is subject to applicable U.S. export controls or sanctions.
4. **Employer/entity authority:** say whether participation is personal or on
   behalf of/in the scope of work for an employer, school, or other entity. If
   it is within such a scope, confirm the entity knows, consents to
   participation and possible prize receipt, and that participation does not
   violate its policies.
5. **Competition-entity status:** confirm whether you are an employee, intern,
   contractor, officer, or director of ARC Prize Foundation, Kaggle, or their
   parent/subsidiary/affiliate entities. Such persons may participate but are
   not prize-eligible.
6. **Account/team status:** confirm that this is your only Kaggle account used
   for the competition and state whether you are already committed to any
   ARC-AGI-3 team or have privately shared ARC-AGI-3 code/data with anyone.
7. **IP and confidentiality:** confirm that work placed in the future
   submission can be licensed and published as required, and will not contain
   employer secrets, third-party confidential material, or material you lack
   the right to submit.
8. **Award obligations:** confirm willingness, if selected, to supply
   eligibility/license/release and applicable tax documents, bear taxes,
   provide reproducible training/inference code and environment details,
   participate in sponsor documentation/interview, and accept the rules'
   publicity/privacy terms.
9. **License authorization:** confirm whether original clean-room software may
   be released under `MIT-0` (or another named permissive OSI license) and the
   winning submission additionally licensed as Kaggle's Rules require under
   `CC BY 4.0`. If not, name the acceptable license or stop the prize track.

## Gate outcome

- Any unknown or negative answer in items 1–3 blocks Entry.
- Missing authority in item 4 blocks work done in that capacity.
- A positive item 5 does not block Entry but blocks prize eligibility.
- Multiple accounts, conflicting team membership, or private sharing in item 6
  requires a separate rules remediation before Entry.
- Unclear IP, confidentiality, publication, or license authority blocks both
  code creation and prize pursuit.
- The campaign state may move from `IDENTITY_BLOCKED` to `ENTRY_READY` only
  after a dated, hash-bound attestation is recorded. That transition authorizes
  **Join only**, not data download, notebook upload, GPU use, or submission.
