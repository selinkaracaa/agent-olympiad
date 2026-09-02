# ARML Local comparison: rules off vs enforced

Same cell: **GPT mini · centralized · arml_local_2009**

| Metric | OLD (`rules off`, Phase B) | NEW (`rules enforced`) |
|---|---:|---:|
| Task score | 26.7/40.0 | 17.8/40.0 |
| Tokens (est.) | 11,281 | 9,278 |
| API calls | 57 | 52 |
| Turns used | 12/12 | 11/30 |
| Chat messages saved | 49 | 51 |
| Chat chars (total) | 40,499 | 34,664 |
| Chat chars (median/msg) | 770 | 655 |
| Chat chars (max/msg) | 2392 | 1185 |

## Takeaway

Enforced rules cap what gets broadcast to teammates (`max_message_chars` on speak/scratchpad actions). Private reasoning stays out of `chat_history`.

- **Inter-agent chat volume:** 14% fewer
- **Total output tokens:** 18% fewer
- **Wall time this run:** ~3 min (11 turns; old run used 12/12)

Transcript: `arml_local/transcripts/arml_local_2009__centralized__enforced.json`
