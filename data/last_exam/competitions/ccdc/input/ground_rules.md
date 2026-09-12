# Ground rules — `ccdc`

Official contestant constraints from `data/rules/ccdc/competition.json`.
This is **input**, not the agent collaboration method.

- Rule id: `ccdc:draft_v1`
- Profile: `non_comparable`
- Protocol: `cyber_defense_proxy`

## Sources

- [NCCDC](https://www.nationalccdc.org/) (not_frozen)
- [https://www.ccdc.io/](https://www.ccdc.io/) (not_frozen)
- [https://www.nationalccdc.org/rules.html](https://www.nationalccdc.org/rules.html) (not_frozen)
- [https://nccdc.org/rules.html](https://nccdc.org/rules.html) (not_frozen)
- [https://neccdl.org/history/2026/resources/Regional-Packet-NECCDC-2026.pdf](https://neccdl.org/history/2026/resources/Regional-Packet-NECCDC-2026.pdf) (not_frozen)

## Contest briefing

National Collegiate Cyber Defense Competition (NCCDC). The task represents a live cyber-defense event through a partial environment. Mixed or unresolved rulesets: the runner permits 8 to 8 active agents and defaults to 8. Collaborate only within the team under contest rules. Banned during the contest: internet access and calculators. Conditional: running code requires the mutable network environment. Paper and pencil are always available. Work only from the materials provided with the problem. Submit one shared defended services and reports; Submit the team's final answers in numbered order, using exact values when required. Treat unexposed physical, oral, live-opponent, judge, timing, or environment mechanisms as unavailable rather than simulated facts.

## Binding contestant constraints

- Do not attack systems outside the authorized scenario environment.
- Live cyber-defense competition: teams operate and defend networked systems under injects; not a paper contest.
- Your institution submits a roster of up to 12 competitors, and the competition team is at most 8 of them, of whom at most 2 may be graduate students.
- Designate a Team Captain as the liaison to the White Team, and keep a captain or identified liaison in the competition space at all times during competition hours.
- Compete with no outside assistance from any non-team member, including your own faculty representative, from the start of the event to the end, overnight hours included.
- Use only Internet resources that are free and available to every team; no fee-gated or membership-gated content, no private staging areas, FTP sites, email accounts, network storage, or shared drives, and no Google Docs or Drive unless competition officials provide it.
- You may use team-written scripts and tools only if they were published on a public, non-university site at least 3 months earlier, declared and frozen with officials, and approved in advance.
- Team-written tools must not reach resources outside the competition environment beyond simple DNS lookups, and must not deliberately break expected system functionality.
- Printed reference materials such as books, magazines, and checklists are permitted; personal computers, laptops, tablets, phones, wireless devices, and removable or electronic media are not, unless pre-authorized.
- Examine only your own systems; any offensive activity against a system outside your assigned network, including another team's, is immediate disqualification.
- Grant Operations and White Team members access to your systems immediately when they ask, and do not modify hardware, open equipment cases, or connect unauthorized devices.
- Do not migrate or containerize a scored service unless an inject or local rule allows it, and accept that any defensive action which breaks the scoring engine is your team's own loss.
- You gain points for keeping required services up, preventing unauthorized access, and completing business injects, and lose them for SLA violations, using recovery services, and successful Red Team penetrations; no running score is shown during play.
- Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing.
