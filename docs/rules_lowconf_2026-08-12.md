# Low-confidence rule cards — primary-source pass (2026-08-12)

Follow-up to [`docs/rules_crawl_2026-08-11.md`](rules_crawl_2026-08-11.md) covering the seven
`competition_id`s whose cards were still low-confidence because the earlier crawl failed,
was blocked, or returned unusable content.

**Method**

- Only organizer-run sites, official rulebooks, and current-season handbooks were treated as
  authority. Where a document was only reachable through a mirror, that is stated explicitly.
- Only constraints that bind a **contestant during the contest** were recorded. Uncertainty and
  unverifiable claims live in `notes`, never in `hard_constraints`.
- No numbers were inferred. Where the organizer publishes a rule only to registered teams
  (Wharton trading requirements, PUMaC per-year calculator policy), that gap is recorded rather
  than filled from secondary sources.

---

## `ichto` — International Chemistry Tournament

**Sources**

- <http://ichto.org/en/rules/> (official rules index; links the current rulebook)
- <http://ichto.org/media/uploads/2025/04/IChTo-2025-rule-book.pdf> (full rulebook, 8th edition,
  labelled "2025 Updated" and still the document linked from the rules page as of this pass)
- <http://ichto.org/en/about/> (role definitions)

**Verified.** The complete rulebook was retrieved and read. Team size is 4–6 students from one
country (§1.5), with up to 2 teams per country. The round structure, the Reporter / Opponent /
Reviewer / Observer roles and their rotation, and the per-segment timings are all specified in a
table in §4.4 that totals 55 minutes: report 8 min, opposition 5 min, reporter's response 4 min,
academic discussion 5 min, review 3 min, jury questions 5 min, general discussion 5 min. Tool
policy is unusually explicit (§1.10–1.11): no electronic devices except calculators, one laptop or
tablet per team for slides only, internet strictly prohibited, no smartwatches or phones, but
mechanical/quartz watches and stopwatches are fine. Communication limits (§4.9–4.11), the
one-role-per-participant rule (§4.8), refusal penalties (§4.5), the single-presentation-file rule
(§4.12), and the full grading scheme (§6, grades 2 to 5+, two extreme grades discarded, Reporter
and Opponent TPs doubled) are all first-party.

**Not verified.** The rulebook is edition-specific (Bucharest 2025); the 2026 edition in
Hoengseong, Republic of Korea may amend timings or penalties, and §8.2 explicitly permits changes.
Appendix 2 grading sheets came through the PDF text extraction badly garbled, so the exact
sub-criterion-to-grade conversion table is not reproduced here.

---

## `wharton_investment` — Wharton Global High School Investment Competition

**Sources**

- <https://globalyouth.wharton.upenn.edu/competitions/investment-competition/rules-roles/>
- <https://globalyouth.wharton.upenn.edu/competitions/investment-competition/>
- <https://globalyouth.wharton.upenn.edu/competitions/investment-competition/faq/>

**Verified.** The General Rules & Roles page was retrieved in full for the 2026–27 season. Teams
are 4–6 students including a designated student team leader, all from the same school; dropping
below four or exceeding six at any point is disqualifying. Each team shares a single Wharton
Investment Simulator (WInS) account and all members trade through it. The advisor must be a
teacher or educator at the school, must register the team (students may not self-register), and
may not make decisions or actively participate in trading or strategy. Paid advisors, education
consultants, agents, and non-Wharton "courses" claiming to teach the competition are prohibited on
pain of disqualification. Contacting the competition client is disqualifying. The two graded
deliverables are the Investment Policy Statement and the Comprehensive Final Report, and the
judging basis is explicitly *not* portfolio performance but strategy quality, alignment to client
objectives, research strength, and clarity of the defense. The generative-AI policy is published:
brainstorming is allowed, submitting AI-generated work as your own is not, and any AI-derived
material must be cited.

**Not verified.** The binding operational detail is deliberately withheld from the public site:
"Detailed instructions for all deliverables, trading requirements, submission deadlines, and
evaluation criteria will be shared with registered teams through SurveyMonkey Apply." So the
required minimum trading activity, the approved-securities universe, the portfolio management
guidelines, the IPS and Final Report deadlines, and the rubric weights are all unavailable without
a team account. Season dates on the public page (competition begins September 28, 2026) are
verified but the deliverable deadlines are not.

---

## `pumac_power` — PUMaC Power Round

**Sources**

- <https://pumac.princeton.edu/competition-rules>
- <https://pumac.princeton.edu/registration-info>

**Verified.** The full Competition Rules page was retrieved. A full team is exactly 8 members, and
all eight may collaborate on the Power Round. The round is released online roughly a week before
the competition date and the team works on it over that week, so there is no in-room clock. The
resource ban is stated as a default that the year's instructions may override: no books, no
internet searches, and no individuals outside the team. Submission mechanics are explicit —
written justification is required and unjustified answers earn nothing, results from earlier parts
may be assumed but must be cited by part and question number, solutions may be handwritten or
typed, printed one side only, each page labelled with team number and problem number, and the team
*name* must not appear anywhere. Only one submission is graded; if a team sends several, the first
received is the one marked. The page also states that instructions printed on the Power Round
itself override the website when they conflict.

**Not verified.** The calculator / computational-aid policy is explicitly year-dependent ("Rules
regarding computational aids vary from year to year and will be specified in the Power Round's
instructions"), and the Power Round instruction sheet for the current season was not retrieved, so
no calculator claim is recorded. Note the site distinguishes the Main Competition's no-tools rule
(individual and team tests) from the Power Round, and those bans do *not* automatically transfer.
The exact submission timestamp has also moved: as of 2023 the round is due at the time printed on
the test and submitted online, rather than on competition day.

---

## `ccdc` — National Collegiate Cyber Defense Competition

**Sources**

- <https://www.nationalccdc.org/rules.html> (2026 national rules, updated 12/10/25)
- <https://nccdc.org/rules.html> (same document, alternate host)
- <https://neccdl.org/history/2026/resources/Regional-Packet-NECCDC-2026.pdf> (regional packet,
  cited only as an example of regional variation)

**Verified.** The complete 2026 national rules text was retrieved. Rosters are up to 12
competitors, the competition team is up to 8 drawn from that roster, and no more than 2 may be
graduate students. Outside assistance from any non-team member — including the team's own faculty
representative — is prohibited from start to end including overnight hours. Internet use is
allowed but only for resources freely available to every team: no fee-gated or
membership-gated content, no private staging areas, FTP sites, email accounts, network storage or
shared drives, and no Google Docs/Drive unless provided by competition officials. Team-written
tooling has a hard three-part gate: published on a public, non-university site for at least three
months beforehand, declared and frozen at submission with officials' approval, and forbidden from
using cloud resources outside the competition environment or from deliberately breaking expected
system functionality. Permitted materials are printed references only; personal laptops, phones,
tablets, wireless devices, and removable media are barred unless pre-authorized. Any offensive
activity outside the team's own network is immediate disqualification. Scoring is service uptime
plus injects, minus SLA violations, recovery-service usage, and successful Red Team penetrations,
with no running totals shown during play and incident reports able to reduce Red Team penalties.

**Not verified.** Nothing material. The national rules explicitly defer some items to a "Local
Competition Rules" section that is per-event, so a specific regional or national event may add
constraints (the NECCDC packet, for instance, freezes the 12-person roster on a fixed date and
caps the team room at eight competitors per day). Event-specific inject schedules and service
lists are not public in advance.

---

## `debatebench` — WUDC / British Parliamentary

**Sources**

- <https://www.worlddebating.org/wudc-manual> (authoritative index; hosts the current Ottawa WUDC
  Debating & Judging Manual)
- <https://www.nwforensics.org/su-debate/WUDC%20Manual%20Oct%2017%202025.pdf> (Sofia WUDC Debater
  & Judge Manual, revised October 2025 — full text read from this mirror)
- <https://esdachronos.nl/uploads/WUDC-2020.pdf> (2020 manual, used to confirm the core rules are
  stable across editions)

**Verified.** Full manual text was read. Four teams of two speakers each (OG, OO, CG, CO) in
speaking order PM, LO, DPM, DLO, MG, MO, GW, OW. Preparation is 15 minutes from motion release,
during which the two speakers must confer solely with each other; assistance from coaches,
institution-mates, or judges is prohibited and can draw disqualification. The electronics rule is
narrow and explicit: devices may be used as stopwatches, as cameras to photograph the draw, motion
and info-slide, and as offline dictionaries — nothing else. Internet research, generative AI, and
online communication with anyone other than the CA team, Organising Committee, or one's partner
are barred without exception, and teams permitted laptops still may not use digital matter files
or shared online documents. Speeches are 7 minutes with roughly a 15-second grace period, after
which judges may not consider anything said. The first and last minute are protected; POIs may be
offered between the 1- and 6-minute marks, last up to 15 seconds, and every speaker must take at
least one or be penalised for failure to engage. Barracking (re-offering within 15 seconds of a
rejection) is disallowed. Judges rank all four teams first through fourth with no draws permitted.

**Not verified.** The current authoritative PDF on worlddebating.org (the Ottawa WUDC 2027
edition) was not itself fetched — the link resolves through a Google Sites file handler. The
constraints above were read from the Sofia 2025 manual and cross-checked against the 2020 manual;
the two agree on every constraint recorded here except that the explicit generative-AI ban appears
only in the 2025 text. Speaker-score scales and the equity/appeal process were not extracted.

---

## `gcch_harvard` — Global Case Competition at Harvard

**Sources**

- <https://www.thecasecompetition.org/gcch-2026>
- <https://www.thecasecompetition.org/>

**Verified.** This is the university-level Global Case Competition at Harvard (11th edition,
thecasecompetition.org), which is a *different* event from the high-school Harvard Crimson Global
Case Competition at casecomp.org; the previous card's source URL (gcchatharvard.com) pointed at the
older domain. Teams are 2–5 students from the same university, individual entry is not allowed,
and one person may appear on only one team. All members must be enrolled for the current academic
year and must supply enrollment documentation or their participation is not confirmed. Round 1 is
a written deck with a work period of up to 3 weeks from case release (Round 1 deadline for the 2026
edition: February 22, 2026, 23:59 ET), and late submissions are not accepted. The top 10 teams
proceed to Round 2, a 5–10 minute recorded video pitch, and then Round 3, a live judge-panel Q&A of
roughly 20 minutes per team covering the case, the submitted deck, and general M&A knowledge.
Judges pick the winners considering all three: deck, video, and finale performance. The case is
finance-oriented and requires industry analysis, company analysis, and financial analysis and
valuation, delivered pitch-book style.

**Not verified.** The organizer publishes no rulebook, terms document, or judging rubric. There is
no public statement on slide or page limits, permitted research sources, software, generative AI,
plagiarism, or whether outside (non-team) help is prohibited. The FAQ page renders as collapsed
accordions and its answers could not be read. Everything above comes from the event and edition
pages rather than a rules document, so this card should be treated as the weakest of the seven.

---

## `qanta` — quiz bowl (NAQT / ACF governing norms)

**Sources**

- <https://www.naqt.com/rules/> (NAQT Gameplay Rules)
- <https://www.naqt.com/downloads/rules.pdf> (same, PDF)
- <https://www.naqt.com/downloads/brief-rules.pdf> (NAQT one-page summary)
- <https://acf-quizbowl.com/rules/gameplay/> (ACF Gameplay Rules)

**Verified.** QANTA is a research dataset built over quiz bowl packets and has no rules of its own,
so the binding norms are those of the two governing bodies, and both full rulesets were retrieved.
They agree on the load-bearing constraints: at most four active players per team at a time,
no conferring while a tossup is live, free conferring on bonuses, and a ban on reference material
during play. NAQT scores tossups at 10 points (15 before the power mark), pairs each correct
tossup with a three-part 30-point bonus that does not bounce back, and assesses a 5-point interrupt
penalty only against the first team to answer incorrectly before the question is finished; answers
are due within 3 seconds of recognition and bonus parts within 5. ACF plays 20 untimed
tossup/bonus cycles with 10-point tossups, 30-point bonuses, the same −5 neg, and additionally
locks a conferring team out of the remainder of a live tossup. On materials, NAQT allows notes a
player writes *during* the game (shareable with teammates on bonuses) but bars reference material
and electronic devices from tables, laps, view, or person; ACF is stricter, allowing only writing
implements and paper that is completely blank, with prepared notes and study aids barred from the
player area entirely. Both bar coaches and spectators from communicating with active players
during play; substitutions are limited to halftime, timeouts, and pre-overtime under NAQT, and to
halftime (or post-regulation ties) under ACF.

**Not verified.** Which ruleset governs any particular QANTA-derived question is undeterminable
from the dataset, since the underlying packets come from many tournaments and formats. Where NAQT
and ACF differ (powers, timed halves vs. 20 untimed cycles, note-taking, substitution windows) the
constraints below record the intersection or flag the divergence rather than picking one.

---

## Machine-mergeable report

```json
{
  "report_date": "2026-08-12",
  "repo": "agent-olympiad",
  "scope": "seven low-confidence rule cards",
  "competitions": {
    "ichto": {
      "best_source_urls": [
        "http://ichto.org/media/uploads/2025/04/IChTo-2025-rule-book.pdf",
        "http://ichto.org/en/rules/",
        "http://ichto.org/en/about/"
      ],
      "hard_constraints": [
        "Teams of 4 to 6 high-school students representing one country; the working language is English.",
        "In each round your team acts as Reporter, Opponent, Reviewer, or (in four-team sections) Observer, and roles rotate every round until every team has held every role.",
        "The Captain nominates which single team member serves as Reporter, Opponent, or Reviewer for a round, and only that person speaks for the team.",
        "Keep to the round clock: report 8 minutes, opposition 5, reporter's response 4, academic discussion 5, review 3, jury questions 5, general discussion 5; all monologues are strictly monologues.",
        "Use no electronic devices except calculators and one laptop or tablet per team for slides; using the Internet is strictly prohibited and costs 30% of the round's technical points after a warning.",
        "The Reporter may open only a single slideshow file and no other files or windows.",
        "Once you begin an active role you may not communicate with your team until the round ends, except during a time-out.",
        "A Captain may call one 60-second time-out per stage, only before the jury's questions and only between parts of the round or during the reporter-opponent discussion.",
        "Take each of Reporter, Opponent, and Reviewer at most once during the semi-finals; extra roles are scored at half technical points.",
        "Your team may reject two challenges per round for free; from the third rejection onward the round's Reporter points are multiplied by 0.8, 0.7, 0.6, 0.5, or 0.4.",
        "Strategic refusals are limited to one per stage and two across all semi-final stages; all other refusals are tactical and apply only to the current round.",
        "In the general discussion each active team may ask exactly one question before observers, jury, and audience may ask."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "The event is a live oral debate with jury scorecards; monologue timing, oratory, and slide quality carry real marks that text-only simulation cannot reproduce.",
        "Grades are given by at least five human jurors with the highest and lowest discarded, which no gold-answer or single-judge proxy reproduces.",
        "Cross-team dynamics (challenge selection, strategic refusals, section grouping by rank) require three or four competing teams running simultaneously."
      ],
      "notes": [
        "Constraints are from the 8th edition (Bucharest 2025) rulebook, which is the document currently linked from ichto.org/en/rules; the 2026 Hoengseong edition may amend them and rule 8.2 explicitly allows changes.",
        "Appendix 2 sub-criterion scoring sheets were garbled in PDF text extraction, so the exact score-to-grade conversion table is not recorded."
      ]
    },

    "wharton_investment": {
      "best_source_urls": [
        "https://globalyouth.wharton.upenn.edu/competitions/investment-competition/rules-roles/",
        "https://globalyouth.wharton.upenn.edu/competitions/investment-competition/",
        "https://globalyouth.wharton.upenn.edu/competitions/investment-competition/faq/"
      ],
      "hard_constraints": [
        "Teams are 4 to 6 students including a designated student team leader, all from the same high school or campus; falling below four or exceeding six at any time is disqualifying.",
        "No student may participate on more than one team.",
        "The team shares one Wharton Investment Simulator (WInS) account and all trades are placed through it.",
        "The student team leader is the sole channel for competition communications and submits all deliverables through SurveyMonkey Apply.",
        "Do not contact the competition client; teams that do are disqualified.",
        "Your advisor is a teacher or educator at your school who guides and registers the team but may not make decisions for you or take part in trading or strategy.",
        "Do not engage paid advisors, education consultants, or agents, and do not enroll in any non-Wharton course claiming to teach the competition.",
        "Produce two graded deliverables: an Investment Policy Statement defining the client's objectives, risk tolerance, and strategy, and a Comprehensive Final Report justifying your strategy, recommendations, and analysis.",
        "Meet the published trading activity and portfolio management requirements throughout the competition.",
        "You may use generative AI only to brainstorm; never submit AI-generated work as your own, and cite any AI-derived material like any other source.",
        "Cite every source you use and do not plagiarize; fabricating analyses, trades, or teamwork narratives is a disqualifying ethics breach.",
        "You are judged on strategy quality, fit to the client's objectives, depth of research and analysis, and how clearly you defend your recommendations — not on portfolio returns."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "The competition runs 10+ weeks against a live market simulator; a turn-budgeted text run cannot reproduce real price movement, trade execution, or portfolio drift.",
        "Advisor guidance is a real but bounded human input with no analogue in the agent roster.",
        "Semifinal and finale rounds are live oral defenses before judges."
      ],
      "notes": [
        "Trading activity minimums, the approved-securities universe, portfolio management guidelines, deliverable deadlines, and the judging rubric are published only to registered teams through SurveyMonkey Apply and could not be verified.",
        "Season-level dates on the public page (competition begins September 28, 2026) are verified, but per-deliverable deadlines are not.",
        "A widely circulated advisor-guidelines PDF states a maximum of seven members; the official Rules & Roles page says four to six, and the official page was used."
      ]
    },

    "pumac_power": {
      "best_source_urls": [
        "https://pumac.princeton.edu/competition-rules",
        "https://pumac.princeton.edu/registration-info"
      ],
      "hard_constraints": [
        "A full team is exactly 8 students, and all eight may collaborate freely on the Power Round.",
        "The Power Round is released online about a week before the competition and is worked on over that week, up to the due time printed on the test.",
        "Use no outside resources unless the test says otherwise: no books, no internet searches, and no people outside your eight team members.",
        "Follow the computational-aid policy printed in that year's Power Round instructions, which is the only authority on calculators and similar aids.",
        "Write full solutions with justification; an answer given without justification earns no credit unless the test states otherwise.",
        "You may use the result of an earlier part even if you could not prove it, but you must cite it explicitly, for example 'From Part II, Question 1'.",
        "Solutions may be handwritten or typed but must be printed on one side of the paper only.",
        "Label every page with your team number and the problem number; your team name must not appear anywhere in the submission.",
        "Submit exactly once; if multiple sets of solutions arrive, only the first received is graded.",
        "Where these rules and the instructions printed on the Power Round conflict, follow the Power Round's own instructions."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "A week-long asynchronous proof-writing effort by eight people maps poorly onto a turn budget.",
        "Proofs are hand-graded for rigor with partial credit, which a gold-answer matcher cannot reproduce.",
        "Formatting rules (one-sided pages, page labelling, anonymity) carry real point deductions but have no analogue in a plain-text submission."
      ],
      "notes": [
        "No calculator claim is recorded because the official page states the computational-aid policy varies year to year and lives in the Power Round instructions, which were not retrieved.",
        "The no-tools bans published for the Individual and Team Tests are separate rules and do not automatically apply to the Power Round.",
        "Submission timing changed as of 2023: the round is due at the time specified on the test and submitted online, not handed in on competition day."
      ]
    },

    "ccdc": {
      "best_source_urls": [
        "https://www.nationalccdc.org/rules.html",
        "https://nccdc.org/rules.html",
        "https://neccdl.org/history/2026/resources/Regional-Packet-NECCDC-2026.pdf"
      ],
      "hard_constraints": [
        "Your institution submits a roster of up to 12 competitors, and the competition team is at most 8 of them, of whom at most 2 may be graduate students.",
        "Designate a Team Captain as the liaison to the White Team, and keep a captain or identified liaison in the competition space at all times during competition hours.",
        "Compete with no outside assistance from any non-team member, including your own faculty representative, from the start of the event to the end, overnight hours included.",
        "Use only Internet resources that are free and available to every team; no fee-gated or membership-gated content, no private staging areas, FTP sites, email accounts, network storage, or shared drives, and no Google Docs or Drive unless competition officials provide it.",
        "You may use team-written scripts and tools only if they were published on a public, non-university site at least 3 months earlier, declared and frozen with officials, and approved in advance.",
        "Team-written tools must not reach resources outside the competition environment beyond simple DNS lookups, and must not deliberately break expected system functionality.",
        "Printed reference materials such as books, magazines, and checklists are permitted; personal computers, laptops, tablets, phones, wireless devices, and removable or electronic media are not, unless pre-authorized.",
        "Examine only your own systems; any offensive activity against a system outside your assigned network, including another team's, is immediate disqualification.",
        "Grant Operations and White Team members access to your systems immediately when they ask, and do not modify hardware, open equipment cases, or connect unauthorized devices.",
        "Do not migrate or containerize a scored service unless an inject or local rule allows it, and accept that any defensive action which breaks the scoring engine is your team's own loss.",
        "You gain points for keeping required services up, preventing unauthorized access, and completing business injects, and lose them for SLA violations, using recovery services, and successful Red Team penetrations; no running score is shown during play.",
        "Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "The contest is a live multi-day defense of real infrastructure against an active human Red Team; no static text environment reproduces adversarial pressure or service uptime scoring.",
        "Injects arrive on an unannounced schedule from an Orange/White Team simulating business customers.",
        "The three-month public-publication requirement for team tooling is an out-of-band preparation constraint that cannot be enforced inside a run."
      ],
      "notes": [
        "These are the 2026 national rules (updated 2025-12-10); each region publishes a Local Competition Rules section that can add constraints, so a specific event may differ.",
        "Event-specific service lists, inject schedules, and scoring weights are not published in advance."
      ]
    },

    "debatebench": {
      "best_source_urls": [
        "https://www.worlddebating.org/wudc-manual",
        "https://www.nwforensics.org/su-debate/WUDC%20Manual%20Oct%2017%202025.pdf",
        "https://esdachronos.nl/uploads/WUDC-2020.pdf"
      ],
      "hard_constraints": [
        "Every debate has four teams of two speakers: Opening Government, Opening Opposition, Closing Government, and Closing Opposition.",
        "Speeches are delivered in the order PM, LO, DPM, DLO, MG, MO, GW, OW, and each speaker gives exactly one speech.",
        "After the motion is released you have 15 minutes to prepare, and during that time you may confer only with your partner.",
        "Take no help from coaches, teammates outside your pair, institution-mates, or judges during preparation; doing so risks disqualification.",
        "Do not use the Internet to research the motion, do not use generative AI for any purpose, and do not communicate with anyone other than your partner, the CA team, or the Organising Committee.",
        "Electronic devices may be used only as stopwatches, as cameras to photograph the draw, motion, and info-slide, or as offline dictionaries; digital matter files and shared online documents are prohibited even for teams permitted laptops.",
        "Be ready to enter the debate room the moment the 15 minutes elapse; a late team can be replaced by a swing team and scores zero for that round.",
        "Speak for 7 minutes; you may finish your sentence or conclusion within roughly 15 seconds, and judges disregard everything said after 7 minutes 15 seconds.",
        "The first and last minute of every speech is protected time in which no POI may be offered; POIs may be offered only between the 1- and 6-minute marks.",
        "Take at least one POI during your speech or be penalised for failure to engage, and keep any POI you offer to 15 seconds or less.",
        "After a POI is refused, wait 15 seconds before any debater on your side offers another; persistent rapid offers count as barracking and are not permitted.",
        "The judging panel ranks all four teams first through fourth by persuasiveness; debates cannot end in a draw."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Live interruption by POIs, protected time, and the 15-second offer window depend on real-time speech that turn-based text cannot reproduce.",
        "Judging is a consensus deliberation among a human panel ranking four teams, not a gold-answer comparison.",
        "Speaker points and the extension obligations of Closing teams depend on what earlier speakers actually said in the room."
      ],
      "notes": [
        "The manual text was read from the Sofia WUDC 2025 revision hosted on a mirror; worlddebating.org is the authoritative index and currently carries the Ottawa WUDC 2027 edition, whose PDF could not be fetched directly.",
        "Every constraint above was cross-checked against the 2020 manual and is stable across editions, except the explicit generative-AI ban, which appears only from the 2025 revision.",
        "Speaker-score scales and the equity and appeals processes were not extracted."
      ]
    },

    "gcch_harvard": {
      "best_source_urls": [
        "https://www.thecasecompetition.org/gcch-2026",
        "https://www.thecasecompetition.org/"
      ],
      "hard_constraints": [
        "Teams are 2 to 5 students from the same university; you may not compete as an individual.",
        "Every member must be enrolled at a university for the current academic year and must supply proof of enrollment or participation is not confirmed.",
        "One person may appear on only one team.",
        "Round 1 deliverable is a written case deck prepared within a work period of up to 3 weeks from case release, and late registrants get only the days remaining before the deadline.",
        "Submit by the published Round 1 deadline; late submissions are not accepted.",
        "The case is a finance and M&A problem requiring industry analysis, company analysis, and financial analysis and valuation, presented pitch-book style.",
        "Only the top 10 teams continue, delivering a recorded video pitch of 5 to 10 minutes that is judged on clarity, synthesis, and presentation quality.",
        "Finalists then face a live judge panel for roughly 20 minutes of Q&A on the case, their submitted deck, and general M&A knowledge.",
        "Winners are chosen by the judges weighing all three of the solution deck, the video pitch, and the finale performance."
      ],
      "confidence": "low",
      "proxy_limitations": [
        "A three-week team research project ending in a slide deck cannot be reproduced by a turn-budgeted text run.",
        "Rounds 2 and 3 are a recorded video pitch and a live oral defense, neither of which is expressible as text output.",
        "Judging is by business executives and HBS faculty against an unpublished rubric."
      ],
      "notes": [
        "This card refers to the university-level Global Case Competition at Harvard (thecasecompetition.org), not the high-school Harvard Crimson Global Case Competition (casecomp.org); the card's previous source URL pointed at the older gcchatharvard.com domain and should be replaced.",
        "The organizer publishes no rulebook, terms document, or judging rubric, so there is no verifiable rule on slide or page limits, permitted research sources, software, generative AI, plagiarism, or outside assistance.",
        "The FAQ page renders answers as collapsed accordions that could not be read, so any detail held only there is unverified.",
        "The February 22, 2026 Round 1 deadline is edition-specific and will change each year."
      ]
    },

    "qanta": {
      "best_source_urls": [
        "https://www.naqt.com/rules/",
        "https://www.naqt.com/downloads/rules.pdf",
        "https://acf-quizbowl.com/rules/gameplay/",
        "https://www.naqt.com/downloads/brief-rules.pdf"
      ],
      "hard_constraints": [
        "At most four players from a team are active at any one time, and only an active player may buzz or answer.",
        "Do not confer in any way while a tossup is live; verbal, written, or signed communication conveying anything about the answer is treated as an incorrect answer for your team.",
        "Confer freely with your active teammates on a bonus, where your team's answer is the first one clearly directed at the moderator.",
        "Do not use reference materials or electronic devices at any point during play, and keep none on your table, in your lap, in view, or on your person.",
        "Notes you write during the game may be used and shared with teammates on bonuses under NAQT rules, but prepared notes and study aids brought from outside are never allowed; ACF play permits only writing implements and completely blank paper.",
        "Buzz first to earn the right to answer, then give your answer within 3 seconds of being recognized.",
        "A tossup answered correctly is worth 10 points and earns your team a three-part bonus totaling 30 points; NAQT additionally awards 15 for a correct answer before the power mark.",
        "Interrupting a tossup before it is fully read and answering incorrectly costs your team 5 points; there is no penalty for a wrong answer after the question has been read in full.",
        "Bonus parts do not bounce back to the other team, and each part must be answered within 5 seconds of being read unless the question specifies otherwise.",
        "Coaches, substitutes, and spectators may not communicate with active players during gameplay, and substitutions happen only at designated breaks such as halftime, a timeout, or before overtime.",
        "Under ACF rules a match is 20 untimed tossup-bonus cycles; under NAQT it is two timed halves of 10 minutes for high school or 11 for college."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Pyramidal tossups are a real-time buzz race against an opposing team; without a live opponent and a buzzer clock, the core scoring mechanic (early buzz versus neg risk) does not exist.",
        "Power marks, 3-second answer windows, and 5-second bonus windows are wall-clock mechanisms with no turn-based equivalent.",
        "Moderator prompting and answer-acceptability judgments are human calls that a string matcher approximates poorly."
      ],
      "notes": [
        "QANTA is a research dataset over quiz bowl packets and publishes no contest rules of its own; the constraints above are the NAQT and ACF gameplay rules that govern the tournaments those packets come from.",
        "Which ruleset applies to any particular QANTA question cannot be determined from the dataset, since the packets span many tournaments and formats.",
        "Where the two bodies differ — powers, timed halves versus 20 untimed cycles, in-game note-taking, and substitution windows — the constraints record the shared rule or name both rather than picking one."
      ]
    }
  }
}
```
