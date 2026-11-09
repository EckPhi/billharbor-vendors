# Issue 16 synthetic channel publication — 2026-11-09

The operator authorized remote publication, protection rules and recovery checks.
No application deployment, vendor activation, real documents or credential values
were used. Sources remain synthetic; real-vendor eligibility stays separately gated.

- [PR #3](https://github.com/EckPhi/billharbor-vendors/pull/3) merged immutable
  upload/retry tooling and a credential-free environment probe into develop.
- [PR #4](https://github.com/EckPhi/billharbor-vendors/pull/4) promoted reviewed
  synthetic sources to main. Stable `v0.5.0` names exact source
  `c5adfedc200d97aff1e8fba9a044e9819325ff82`.
- [Alpha run](https://github.com/EckPhi/billharbor-vendors/actions/runs/42595888526)
  published `v0.5.0a16001`; [beta run](https://github.com/EckPhi/billharbor-vendors/actions/runs/42596185886)
  published `v0.5.0b17001`; [stable run](https://github.com/EckPhi/billharbor-vendors/actions/runs/42596308753)
  and its exact-source retry both passed without replacing asset bytes.
- The previously denied [develop run](https://github.com/EckPhi/billharbor-vendors/actions/runs/42530099942)
  succeeded on attempt 2 after corrected branch policy and owner approval.
- Pages now allows main/develop branches and v* tags, requires owner EckPhi review,
  and disables admin bypass. Self-review is permitted for this single-owner project.
  [Main probe](https://github.com/EckPhi/billharbor-vendors/actions/runs/42596593775)
  waited for approval and passed; [task-branch probe](https://github.com/EckPhi/billharbor-vendors/actions/runs/42596303437)
  was denied before any step executed.
- Tag publication retained the correct Pages artifact while public responses
  briefly served earlier bytes. [Main-only reconstruction](https://github.com/EckPhi/billharbor-vendors/actions/runs/42597794923)
  resolved that mismatch. [Repeated reconstruction](https://github.com/EckPhi/billharbor-vendors/actions/runs/42598338658)
  renewed all feed revisions and preserved all 21 current/historical artifact URLs
  checked against their pre-recovery hashes. Workflow success alone is not public
  acceptance; check canonical HTTP bytes after publication.

[Alpha](https://eckphi.github.io/billharbor-vendors/alpha/index.json),
[beta](https://eckphi.github.io/billharbor-vendors/beta/index.json) and
[stable](https://eckphi.github.io/billharbor-vendors/stable/index.json) are available.
Root follows beta byte-for-byte; channel identities remain distinct. The engine's
scoped issue-16 evidence retains exact index/descriptor/wheel/manifest digests,
expiry, SDK and source identities. Integrity verification never approves trust,
installs/selects a package or enables an account.

No dependency, action pin, license or credential scope changed. Rollback uses
retained immutable releases/URLs and prior reviewed installation locks. Recovery
reconstructs ledgers and renews metadata; never rewrite a released wheel or ledger.
This documentation handoff changes no public artifact or application state.
