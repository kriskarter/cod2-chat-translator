# Candidate checkpoint

Base commit 7e63e21b67f262aa843e77bea85b6980263ce247. Candidate revision is the commit containing this entry. Both Windows jobs run on branch push.

All 409 private export rows were reviewed locally. They represent 676 observations (638 incoming, 38 outgoing). Of 145 failed observations, 140 were offline, four were rejected during semantic checks and one was attributed to online services.

| Primary review category | Rows | Observations |
|---|---:|---:|
| Already in target language | 18 | 80 |
| Plausible meaning | 173 | 335 |
| No result, other categories excluded | 24 | 44 |
| Commands or technical fragments | 8 | 14 |
| Emotions | 35 | 42 |
| Possible partial drafts | 12 | 15 |
| Names in context | 58 | 60 |
| Ambiguous | 55 | 57 |
| Short or language-sensitive | 12 | 14 |
| Game context | 14 | 15 |

Same offline replay before and after: 78 → 105 locally resolved rows, 163 → 259 weighted observations. These measure local coverage, not semantic accuracy. All eleven selected problem phrases resolved locally after the change. Pack v4 contains 227 entries. Shared distribution stays at v3 pending acceptance.

Local suite: 322 passed, 7 skipped, 57 subtests passed. WAL migration merged committed observations from two profiles exactly once, excluded an open transaction and passed integrity_check. Other changes include manual ZIP export, suggested dated name, privacy filtering, SQLite counts, opt-in experience recording and background dictionary refresh.

Release gates: verify both Windows results on the candidate commit, installer checksum, signed update manifests, and the original v1.17.4 update flow. Existing installer CI exercises installation over the original release; this alone does not prove in-app update discovery. Keep PRs in draft until owner acceptance. Review the chain PR 9 → premium-ui-redesign (PR 8) → wwii-simple-home-rc4 → main before merging. Build and verify the actual merge SHA before activating stable.

Second checkpoint follows 8b1814d09506088a9e3650fbc2fbd1426c3242c7. Added the v1.17.4-compatible Qt ZIP and legacy manifest. Installer CI invokes the original shipped updater against a file URI and checks the installed binary digest. This exercises the updater separately from release discovery. Production signature verification and public discovery require the approved signing/release workflow. An installation upgraded through ZIP retains the old Windows uninstall registration until the full installer runs. Run the verified installer in the same folder to refresh registration. Standalone Linux synthetic guard 32/32. Two-worker burst p95 was 410 ms with a 50 ms simulated provider.
Final local run: 323 passed, 7 platform skips, 69 subtests passed. The screenshots in the three galleries are captures from the running localized application.
