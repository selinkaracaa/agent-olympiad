# `data/last_exam`

Generated Agents' Last Exam layout. Canonical sources stay in `data/rules`
and `data/benchmarks`. `data/base` is a previous generator output.

```bash
python collectors/build_last_exam_from_rules.py
```

## Layers

| Layer | Path | Audience |
|---|---|---|
| Input | `competitions/<cid>/input/` | Agent at start: official ground rules |
| Method | `competitions/<cid>/method/` | Agent at start: how this benchmark's team works |
| Problem | `tasks/<cid>/<pid>/base/input/` | Agent at start: this problem only |
| Eval | `competitions/<cid>/eval/` and `tasks/<cid>/<pid>/eval/` | Hidden until grade |

Tasks do not copy `collaboration.json`. They inherit `competitions/<cid>`.
Gold answers stay in `data/benchmarks` and are only pointed at from `eval/`.
