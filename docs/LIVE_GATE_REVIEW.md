# Review the configured live gate

Add project keys only to ignored `.env`: MODEL_PROVIDER=deepseek, DEEPSEEK_API_KEY, DEEPGRAM_API_KEY, CARTESIA_API_KEY and CARTESIA_VOICE_ID (or explicitly select OpenAI with its own key). Run `scripts/check-live.ps1` sequentially; provider calls may consume account credits. Do not replace a failed output with a fixture result.

Review `phase-08-live-providers.json` and the model/speech reports: exact recognized source, speaker attribution, cited proposal and date/place/owner, no fabricated clinical confirmation/order/completion, shared closeout wording, interruption cancellation, separate approvals and actual sandbox receipt. Test files retain original synthetic text only; use no patient data.

Metrics distinguish: (1) recognition/extraction/action pipeline timing from timestamps; (2) twenty-trial speech startup proxy and stop-to-silence; (3) unwanted interruptions counted from observed speech events, including zero only if observed; (4) selected unanswered priorities from saved state; (5) unsupported assertions reviewed against exact quotes rather than inferred from test pass; (6) actual completed action receipts and unknown/rejected work. Mark missing measures unverified. An assertion of hearing is never inferred from publisher playout.

The earlier offline p95 startup proxy was 3,127 ms and missed the roughly 2,000 ms target; stop-to-silence was 473 ms and met 500 ms. Do not infer improvement from the recovery fixes. Physical acoustics, accents, listening quality and human acceptance require separate sessions. Final phase status remains conditional until the configured end-to-end output and timing results are reviewed.
