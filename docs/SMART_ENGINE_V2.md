# Smart Engine V2 — v1.19.0 release candidate

## Product contract

- Existing F8, F9, Classic and Smart V1 remain available. The main **Smart** checkbox disables Smart entirely; **Knowledge → Enable V2 knowledge** disables only V2 extensions.
- No paid LLM, key, signup, extra translation backend, or game-process modification.
- F8/F9 first probe the entire local path (V1 direct forms, V2 exact multilingual aliases, validated tactical templates, optional exact cache). They bypass the slow network worker queue when possible. F8 uses 80 ms log polling and 40 ms UI polling; F9 shows local previews before the 180 ms network debounce. Network requests still need live Internet.
- Two bounded workers retained per direction; Google transport failures trigger a short shared cooldown (after two failures; 10 s); MyMemory is preferred briefly and Google remains fallback. No speculative parallel doubling of network requests.
- Only exact or tightly validated patterns; no broad approximate replacement. RU/UK/EN primary, common PL/DE/FR/ES/TR phrases. Explicit same-speaker context snapshots follow log arrival order and expire after 8 seconds; map/log changes invalidate old results. Contextual low requires a preceding explicit HP fragment; unknown context remains unknown. V1 safety gates still apply. Sarcasm, arbitrary intent and all languages are not solved by this local data system.
- On failed F8 online lookup, show original with warning instead of hiding it; F9 never automatically sends an invalid translation.

## Personal experience (optional)

Open **Knowledge**. Enable local example collection and/or temporary disk cache if desired.
Both switches default OFF. Existing online translation behaviour is unchanged. No automatic uploads. Collection includes accepted F9 previews, even drafts not sent to the game, as well as F8 messages after duplicate filtering, current translation or failure, route, timing, count and at most two short same-speaker preceding snippets. No explicit nickname, server, device or raw-log fields. Obvious identifiers/credentials are excluded, and the current author's nickname is removed where detectable. Free text may still contain personal information; review exports before sharing.

The SQLite file is in the application settings directory. A single bounded background writer performs disk work; queues can drop observations under overload, but never block translation. Cache is exact key/version/direction/source/target/style, only accepted MT output, temporary and opt-in, NOT authoritative knowledge. Limit 3,000 cache records and 7 day TTL; 10,000 unique examples and 30 day retention; timing sample ring last 4,096 records, 30 day retention. Periodic pruning (up to 31 transient extra rows before batch prune); export prunes first. UI offers statistics with p50/p95, clear experience, and manual ZIP export. Cache/context are not sent to a server. On abrupt shutdown uncommitted observations may be lost.

ZIP contains manifest.json, examples.jsonl, metrics.json; no automatic upload. Metrics cover measured application processing from F8 enqueue or F9 request start, not actual game/server transport or typing time. F8 log polling/render overhead is not fully included. F9 records completed current previews; canceled previews excluded. Timing-only measured samples may include privacy-filtered messages, without content.
Run offline:
    python tools/analyze_experience.py path/to/CoD2-knowledge.zip

Curate new phrases manually from reviewed, consented exports. Do not turn all MT outputs into published translations. No user ZIP, private examples or SQLite files are committed to the public repository.

## Shared knowledge channel

Bundled assets/knowledge_v2.json is the safe baseline. Data-only branch **knowledge-v2** contains the same file. App checks the fixed HTTPS URL at startup (optional) or by button; download is outside the translation path, capped at 1 MiB, strictly parsed, no redirects, monotonically higher version only, written atomically and swapped in memory. Old/broken/unavailable data leaves the previous pack working. Update only the data branch after local validation/review; code updates use separate RC/release gates. Trust is based on HTTPS and the controlled repo, not an independent cryptographic signature. Never publish raw collected chat. To release new knowledge, increment integer version and run full tests, semantic gate, pack checker and benchmark, then commit reviewed data to the data branch without changing the main app branch.

## Validation

- Seed pack: 195 curated authored phrase groups (roughly one thousand spellings/forms plus exact templates). These are draft authored knowledge, not a corpus independently verified by native speakers. Coverage on real servers is not yet known.
- Synthetic offline reference set: 22 authored cases, ideal 50 ms provider stub; Classic and V1 route 19 requests online, V2 routes 3. All 22 reference matches in these curated cases. This measures routing and simulated time, not actual translation accuracy or live network.
- Unit tests include persistence, privacy filtering, manual ZIP, version rollback, stale data, F8 queue bypass, F9 local route, fallback health, context and tactical preservation.
- User must test Windows RC F8/F9 on real CoD2, including FPS, latency, collect/export, provider failure, style/mode switching and knowledge updates. No stable release, tag or merge before real playtest/approval. See RELEASE_PROCESS.md.
