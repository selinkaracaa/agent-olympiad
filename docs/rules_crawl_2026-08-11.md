# Official Contestant Rules Crawl — 2026-08-11

Read-only research of **primary official** contestant-facing constraints for every `competition_id` in `data/benchmarks/index.json` (37 tracks). Prioritized sources already listed in `docs/DATA_COLLECTION.md` Simulator Matrix and `data/rules/*.json` `provenance.sources`.

**Method notes**

- Claims below are tied to fetched official pages/PDFs or explicitly marked as **not retrieved**.
- Repo rule cards (`data/rules/*.json`) were used only as leads / cross-checks, not as authority.
- Thoroughness: **very thorough** on paper contests and programming; **medium** on rubric / oral / physical tracks.
- Do not treat this file as a substitute for year-specific host packets (especially lab/robotics/CTF).

---

## Report keyed by `competition_id`

```json
{
  "crawl_date": "2026-08-11",
  "repo": "agent-olympiad",
  "index": "data/benchmarks/index.json",
  "competitions": {

    "ijso_practical": {
      "name": "International Junior Science Olympiad — Practical (Team)",
      "best_source_urls": [
        "https://ijsoweb.org/qna/IJSO-Statutes-Qatar-2019.pdf"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Practical Examination is a team event: each country may field two practical teams of 3 students each (from the up-to-6-student national delegation).",
        "Each examination (MCQ / Theory / Practical) is normally 3–4 hours; practical is experimental (physics/chemistry/biology combined).",
        "Practical scoring: 40 points (MCQ 30 + Theory 30 + Practical 40); all members of a practical team receive the same practical points.",
        "Organizers provide calculators with simple statistical functions; using own calculators is not allowed (point deduction / ban).",
        "Leaders/observers may not contact contestants about discussed problems until those exams finish.",
        "Submission: experimental lab report work (data, calculations, tables/graphs) on provided practical materials; marking by Scientific Committee with moderation."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Physical wet-lab equipment, specimens, and timed instrument handling cannot be faithfully simulated from PDF protocols alone.",
        "Point deductions for personal calculators / equipment complaints are host-operational and hard to proxy."
      ]
    },

    "ieo_business_case": {
      "name": "International Economics Olympiad — Business Case",
      "best_source_urls": [
        "https://files.ieo-official.org/IEO_Regulations_of_Competition.pdf",
        "https://files.ieo-official.org/IEO_Syllabus.pdf"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team size: ≤5 contestants (+1–2 leaders).",
        "Business Case is a team competition; communication only with IEO officials and teammates (no outsiders).",
        "Business Case lasts two days: preparation day + presentation day; presentations must be English slide-supported oral talks.",
        "During preparation: any online and offline materials allowed; contacting other people for help is prohibited.",
        "All teams submit slides by Steering Committee deadline before Opening Ceremony; no slide changes afterward.",
        "Business Case contributes 50 final points (raw then Z-normalized); group stage then Finals for group winners; criterion scores use median of judges.",
        "Contrast: Economics/Finance individual exams ban smartphones/electronics; permitted instruments listed ≤1 month ahead (not the Business Case tools regime)."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Oral Q&A with live judge panels and slide-lock social dynamics are weak under text-only multi-agent simulation.",
        "Case partner / host-specific scoring guide is not universal across years."
      ]
    },

    "iol_team": {
      "name": "International Linguistics Olympiad — Team Contest",
      "best_source_urls": [
        "https://ioling.org/rules/rules.pdf",
        "https://ioling.org/guidelines/en/"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Delegation/team size: ≤4 contestants (+ team leader).",
        "Team contest: members work jointly on one problem set; normally 4 hours; each member gets a copy; team submits a single solution.",
        "Free verbal collaboration within the team room.",
        "Same material/device bans as individual contest: no printed matter/dictionaries; no own paper; no phones/laptops/tablets/smartwatches or outside-world devices; organizer writing paper only; pens preferred.",
        "Artificial aids such as pocket calculators should not be brought (regulations).",
        "Problems on paper; explanations required unless instructed otherwise; one working language for the team solution."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Wall-clock 4h and quiet shared room dynamics map poorly to turn budgets.",
        "Handwritten diagram/script linguistic answers lose fidelity in plain text."
      ]
    },

    "ioaa_group": {
      "name": "International Olympiad on Astronomy and Astrophysics — Group Competition",
      "best_source_urls": [
        "https://www.ioaa2026.vn/en/ioaa-statutes",
        "https://cdn.ioaastrophysics.org/assets/IOAA%20problems/16th%20IOAA%202023/Group%20Competition%202023%20IOAA.pdf",
        "https://ioaastrophysics.org/current-ioaa/for-participants"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Statutes: group teams of ≥5 students, each from a different country, randomized when possible.",
        "2023 Group Competition instructions (representative packet): 5-person random asteroid teams; max 90 minutes; win by shortest total time after time penalties; no communication with other teams.",
        "Everything needed provided on table: calculator, office supplies, geometrical instruments, paper, constants table (2023 packet).",
        "Dedicated answer sheets; final answers in marked boxes; sealed envelopes opened on START.",
        "National individual theory/practical statutes separately allow drawing materials + non-programmable calculators / host-provided calculators (year-dependent; e.g. IOAA 2026 host provides CASIO fx-82CW only) and ban formula collections — group round uses organizer-provided kit."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Time-ranked scoring with penalties needs a real wall clock and answer-sheet workflow.",
        "Star charts / geometric instruments / provided calculator model quirks are underspecified in text simulation."
      ]
    },

    "arml_power": {
      "name": "ARML Power Contest",
      "best_source_urls": [
        "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public",
        "https://www.arml.com/ARML/arml_2019/page/index.php?page=5&page_type=public&show_page=samples",
        "https://www.arml.com/ARML/arml_2019/page/index.php?page=5&page_type=public&show_page=rules"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "National ARML competition rules (shared tool bans): calculators not allowed on any part of ARML; electronic devices banned (phones/computers/tablets/etc.); Power Round worth 50 points; teams may submit exactly one solution to the Power Question (extra solutions → lowest score kept).",
        "Power Contest is a separate mail/in-school proof contest series (Fall/Spring problem PDFs published); dedicated Power Contest Rules page currently shows 'Under Construction'.",
        "Administrivia PDF for Fall 2025 listed on samples page but fetch timed out in this crawl — treat team size/time window as year-packet-specific until that PDF is retrieved."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Without the Power Contest administrivia PDF, roster size and sit time for the standalone Power Contest are not confirmed from primary text.",
        "Proof handwriting / single-packet submission discipline is easy to under-enforce for agents."
      ]
    },

    "arml_national_team": {
      "name": "ARML National Meet — Team Round",
      "best_source_urls": [
        "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team of 15 members (may compete with fewer; Relay handling special-cased).",
        "Team Round: 10 questions; 5 points each; 50 points possible.",
        "No calculators on any ARML part; no electronic devices (discovery during Team/Power → disqualification from that round).",
        "Paper dictionary allowed only for non-native English speakers (book form; no electronic translators).",
        "No substitutions once Team Round has started; free collaboration implied for Team Round (contrast Relay/Individual communication bans).",
        "Submission: team answers for Team Round (short answers)."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "15-agent coordination cost and physical card/proctor logistics are heavy to simulate.",
        "Exact Team Round wall-clock duration not stated on the fetched competition-rules page (needs site schedule/packet)."
      ]
    },

    "arml_national_power": {
      "name": "ARML National Meet — Power Round",
      "best_source_urls": [
        "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Same 15-person team context as national meet.",
        "Power Round worth 50 points; exactly one solution packet may be submitted (multiple submissions → lowest score).",
        "No calculators; electronic devices banned during Team/Power (devices collected before Team, returned after Power).",
        "Written proofs / justifications expected for Power problems (contest design; scoring structure on rules page)."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Wall-clock Power Round duration not on the fetched rules page.",
        "Single irrevocable packet + handwriting fidelity."
      ]
    },

    "arml_local": {
      "name": "ARML Local",
      "best_source_urls": [
        "https://www.arml.com/ARML/arml_2019/page/index.php?page=6&page_type=public&show_page=main_page",
        "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Teams of six students; schools may field multiple teams.",
        "Team Round: 45 minutes; set of 15 short-answer questions worked by the entire team together.",
        "Also Individual (5×10 min pairs) and Relay (6/8/10 min structures) — benchmark track focuses on team round.",
        "National no-calculator / no-electronics bans apply across ARML contests; Local inherits paper/pencil only expectation.",
        "Coaches/local coordinators grade and submit scores."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Local scoring (4 pts × 15 = 60 in many regional mirrors) is consistent with secondary mirrors but confirm against current ARML Local Google Doc if linked from site.",
        "45-minute hard stop is the main timing proxy gap."
      ]
    },

    "wsc_writing": {
      "name": "World Scholar's Cup — Collaborative Writing",
      "best_source_urls": [
        "https://scholarscup.org/events/",
        "https://www.dropbox.com/scl/fi/5cxl9ri1lziscxvnufxnv/Collaborative-Writing-Rubric.pdf?rlkey=5hs28p3rlk6jdlvrgneioueka&dl=1"
      ],
      "retrieved": true,
      "hard_constraints": [
        "The team receives three to four prompts drawn from the six World Scholar's Cup subject areas.",
        "The team answers exactly three prompts.",
        "Each of the three teammates answers a different prompt.",
        "First prepare with teammates without using devices, then write independently, then review one another's work at the end.",
        "Write the response with pen or pencil.",
        "Responses may use a form appropriate to the prompt, including creative pieces, persuasive arguments, poems, or essays."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Neither the fetched official events page nor the official rubric PDF states a numeric stage schedule.",
        "The rubric PDF contains evaluation questions only; it does not establish a rule that peer editors may not finish an incomplete response."
      ]
    },

    "jessup": {
      "name": "Philip C. Jessup International Law Moot Court Competition",
      "best_source_urls": [
        "https://www.ilsa.org/History/Jessup%202027/Jessup%202027%20Official%20Rules.pdf",
        "https://www.ilsa.org/jessup-competitors/jessup-faq/",
        "https://www.ilsa.org/jessup/"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team: 2–5 Team Members; only Team Members may contribute substantive work product.",
        "Outside assistance tightly limited: research/write/edit of Memorials and oral arguments must be exclusive Team Member work; Advisors limited to general advice (research methods, writing/advocacy technique) not drafting arguments.",
        "Memorials: Applicant + Respondent; hard submission deadline (disqualification if missing both by schedule time); formatting/content rules in Rule 5.",
        "Season roughly Compromis in September → memorials ~January → oral Qualifying/International rounds.",
        "No other-team assistance (notes, memorials, practice moots against competitors, etc.).",
        "FAQ confirms max five contributors over the competition year."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Months-long research + proprietary legal databases (ILSA-provided) are not free-web equivalent.",
        "Oral courtroom advocacy and anonymity rules are out of scope for written-memorial-only agent evals.",
        "AI policy: not a blanket ban in the sections reviewed; still subordinate to exclusive Team Member work-product rule — do not invent a permission."
      ]
    },

    "iiot": {
      "name": "International Informatics Olympiad in Teams (IIOT)",
      "best_source_urls": [
        "https://iio.team/documents/Regulations.pdf",
        "http://iiot2026.cni.nt.edu.ro/online-participation-rules/"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team: 4 students (+2 reserves); same school/region constraints per regulations.",
        "International Final: 4 hours, ≥7 problems; English problem statements.",
        "Only organizer-provided computers/software; own mouse/keyboard if approved; USB disabled; Internet only to contest platform.",
        "Regulations list allowed languages C, C++, Pascal with language docs available; host publishes OS/IDE list ≥1 month ahead.",
        "IIOT 2026 online participation rules: 2 computers per team; Internet limited to grading system; **only C++ accepted for submissions** (host-year restriction stricter than general regulations).",
        "National contests: no phones/tablets/personal electronics; no textbooks/translators; no inter-team communication.",
        "Submission: source programs to automatic evaluator."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Prefer year-host environment (2 VMs, C++-only) over older multi-language regulations when simulating recent Finals.",
        "Shared dual-workstation contention is a core team-programming constraint agents often ignore."
      ]
    },

    "icpc": {
      "name": "ICPC — International Collegiate Programming Contest",
      "best_source_urls": [
        "https://docs.icpc.global/worldfinals-programming-environment",
        "https://icpc.global/worldfinals/on-site-registration",
        "https://euc.icpc.global/home-2026/rules/"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team of 3 contestants; one shared workstation (World Finals traditional setup).",
        "Languages: C, C++, Java, Kotlin, Python 3 (WF environment page); EUC 2026 same set; 5-hour contest (EUC rules).",
        "No additional computers/electronics/calculators/screens in Team Area; no Internet on contest machines (practice images may have net; WF does not).",
        "Team Reference Document ≤25 single-sided pages (printed only; not on machine); one printed natural-language dictionary per person, unannotated.",
        "IDE internal AI tools disabled on WF image.",
        "Scoring: ICPC WF rules — # solved then time penalty; compile errors not penalized (EUC); scoreboard freeze last hour (EUC).",
        "Communication only among team members (+ staff for clarifications/tech)."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "One keyboard / three humans is the dominant constraint; multi-agent parallel coding overstates capability.",
        "Exact WF duration is in regional/WF contest rules (EUC states 5h; confirm current WF rules PDF for the evaluated year)."
      ]
    },

    "cfa_research_challenge": {
      "name": "CFA Institute Research Challenge",
      "best_source_urls": [
        "https://www.cfainstitute.org/sites/default/files/-/media/documents/support/research-challenge/challenge/research-challenge-official-rules.pdf",
        "https://www.cfainstitute.org/sites/default/files/docs/insights/events/rc-faculty-advisor-guidelines.pdf"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team: 3–5 students at local kickoff; no alternates; undergrad/grad mix allowed.",
        "Only team members may research the subject company; publicly available information only.",
        "May use faculty advisor + industry mentor within timed caps (faculty ≤10h advisory before written report; mentor time capped in Rule 3.4); may not enlist other professionals to do the analysis.",
        "AI allowed only with reflective/responsible disclosure (Appendix B); misrepresenting AI output as own analysis prohibited.",
        "Deliverables: written equity research report + oral presentation to judges; local scoring often 50% written / 50% presentation.",
        "Plagiarism ban; cite sources; IP/copyright obligations on third-party materials."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Paid terminals (Bloomberg etc.) and company info sessions are not freely replicable.",
        "Mentor hour caps and oral defense Q&A are hard to simulate honestly."
      ]
    },

    "eoes": {
      "name": "European Olympiad of Experimental Science (EOES / EUSO)",
      "best_source_urls": [
        "https://www.eoes.science/index.html",
        "https://www.eoes.science/page/documentsEOES.html"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Official home page: each country sends two teams of three; two experimental assignments spanning biology/chemistry/physics skills.",
        "Age: may only turn 17 during the EOES year (never older than 17).",
        "Emphasis on team division of labor; ~4 hours per assignment described on home page.",
        "GB-adopted Rules & Regulations / Guidelines / Syllabus documents are linked from documents page but the fetch did not return downloadable PDF bodies in this crawl — open those PDFs from the documents page for instrument bans and exact timing."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Wet-lab / instrument practicals are non-comparable to PDF reading agents without a lab proxy.",
        "Rules PDF content not fully retrieved here."
      ]
    },

    "ethics_bowl_appe": {
      "name": "APPE Intercollegiate Ethics Bowl",
      "best_source_urls": [
        "https://www.appe-ethics.org/cases-rules-guidelines/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Official hub hosts current case sets plus Rules/FAQs/Guidelines and judge scoring guides.",
        "Format (from official training materials titles): moderated oral rounds with judge questions and scoring sheets — not a written exam.",
        "Team size commonly up to 5 in community practice; confirm exact roster limits in the linked Rules PDF on the same page (not fully extracted in this crawl)."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Live oral ethics debate / commentary rounds are rubric-oral; transcript-only proxies lose timing and interruption norms.",
        "Need the Rules PDF click-through for bans on notes/devices if any."
      ]
    },

    "ethics_bowl_nhseb": {
      "name": "National High School Ethics Bowl",
      "best_source_urls": [
        "https://nhseb.org/case-library",
        "https://nhseb.org/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Official case library publishes retired National/Regional case sets under Creative Commons for prep.",
        "Competition uses case-based oral ethics bowl format (same family as APPE); detailed timing/roster rules live in NHSEB competition rules (not fully fetched from case-library page)."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Oral presentation + commentary + judge Q&A cannot be reduced to static essay answers without acknowledging the format mismatch."
      ]
    },

    "ichto": {
      "name": "International Chemistry Tournament (IChTo)",
      "best_source_urls": [
        "http://ichto.org/en/problems/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Official problems page publishes annual problem sets for a chemistry tournament (oral fight / reporting style historically).",
        "Index lists team_size 3; confirm roster, fight timing, and allowed aids from current IChTo regulations if published on ichto.org (regulations PDF not confirmed in this crawl)."
      ],
      "confidence": "low",
      "proxy_limitations": [
        "Tournament oral fights (Reporter/Opponent style) are poorly approximated by silent collaborative writeups.",
        "Primary regulations PDF not retrieved — do not invent fight clocks or bans."
      ]
    },

    "pumac_power": {
      "name": "PUMaC Power Round",
      "best_source_urls": [
        "https://pumac.princeton.edu/",
        "https://jason-shi-f9dm.squarespace.com/archives"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "PUMaC is Princeton Math Club’s annual contest with Individual, Team, and Power rounds; Power is proof-based and weighted in team standings (weighting lowered for 2025+ per site).",
        "Public site schedule/embed did not expose numeric Power Round duration, calculator policy, or roster size in fetchable HTML.",
        "Index uses team_size 8 — treat as provisional until official coach packet / rules sheet for the evaluated year is obtained."
      ],
      "confidence": "low",
      "proxy_limitations": [
        "Without the year packet, do not invent calculator bans or Power Round minutes.",
        "Proof partial-credit culture differs from short-answer math contests."
      ]
    },

    "vis_moot": {
      "name": "Willem C. Vis International Commercial Arbitration Moot",
      "best_source_urls": [
        "https://www.vismoot.org/wp-content/uploads/2023/09/31st-Vis-Moot-Rules_FINAL.pdf",
        "https://www.vismoot.org/"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team: ≥2 students from one institution; no maximum team size (31st Rules §31).",
        "Parts: memorandum for claimant, memorandum for respondent, oral hearings.",
        "Memoranda: searchable PDF, single file, typically ≤1 MB upload limit; deadlines via team account (claimant then respondent).",
        "Facts limited to Problem + clarifications + necessary logical extensions / publicly available true facts; inventing facts is unethical and sanctioned.",
        "Oral hearings in Vienna (and/or Vis East Hong Kong as separate moot); registration fee and participation expectations after claimant memo.",
        "Use current-year Rules Booklet (rules change annually)."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Index team_size 5 is a modeling choice, not a Vis maximum.",
        "Oral arbitration advocacy and multi-month prep dwarfs single-session agent runs.",
        "31st Rules PDF retrieved; prefer the Rules Booklet for the exact Vis year under evaluation."
      ]
    },

    "wharton_investment": {
      "name": "Wharton Global High School Investment Competition",
      "best_source_urls": [
        "https://globalyouth.wharton.upenn.edu/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Official Global Youth portal hosts the Investment Competition; detailed team size/time/tool rules are in season-specific competition guidelines (not fully extracted from the portal root fetch).",
        "Index lists team_size 5 — confirm against current season PDF/FAQ before treating as hard."
      ],
      "confidence": "low",
      "proxy_limitations": [
        "Market-data platforms, mentor rules, and presentation rounds need the season packet.",
        "Do not invent AI or internet bans without the official guidelines."
      ]
    },

    "ccdc": {
      "name": "National Collegiate Cyber Defense Competition (NCCDC)",
      "best_source_urls": [
        "https://www.ccdc.io/",
        "https://www.nationalccdc.org/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "nationalccdc.org redirects to ccdc.io (official site moved).",
        "Live cyber-defense competition: teams operate and defend networked systems under injects; not a paper contest.",
        "Exact roster caps, tooling, and collaboration rules must be taken from current CCDC / regional handbooks on ccdc.io (not fully retrieved in this crawl).",
        "Benchmark materials are Team Packets / Wildcard scenario briefs only — live VMs/injects excluded by collection strategy."
      ],
      "confidence": "low",
      "proxy_limitations": [
        "Packet-only evaluation is explicitly a proxy for live blue-team operations.",
        "Index team_size 8 is a modeling default pending official handbook confirmation."
      ]
    },

    "debatebench": {
      "name": "DebateBench (WUDC / BP)",
      "best_source_urls": [
        "https://www.worlddebating.org/",
        "https://huggingface.co/datasets"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Benchmark is a cleaned British Parliamentary debate corpus, not itself a governing body.",
        "BP/WUDC norms (secondary to official WUDC rules): 4 teams of 2 in a room; limited prep after motion release; no internet during prep in many championship settings — verify against current WUDC Debating & Judging Rules for the simulated format.",
        "Repo provenance currently points at Hugging Face datasets — treat as benchmark-native, not official regulations."
      ],
      "confidence": "low",
      "proxy_limitations": [
        "Transcript scoring ≠ live BP judging (POIs, timing bells, speaker ranks).",
        "Must cite WUDC rules PDF explicitly before claiming official_equivalent."
      ]
    },

    "gcch_harvard": {
      "name": "Global Case Competition at Harvard",
      "superseded_by": "docs/rules_lowconf_2026-08-12.md",
      "best_source_urls": [
        "https://www.gcchatharvard.com/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Official site hosts case competition; typical deliverable is team case presentation/paper.",
        "Detailed roster/time/tool constraints not extracted from homepage fetch — use year packet / rules tab if present.",
        "Index team_size 4 provisional."
      ],
      "confidence": "low",
      "proxy_limitations": [
        "Consulting-style oral finals and slide decks need rubric + timing from organizers."
      ]
    },

    "history_olympiad": {
      "name": "International History Olympiad / IHBB — History Bowl",
      "best_source_urls": [
        "https://www.historyolympiad.com/resources/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Resources page hosts past Bowl packets (tossup/bonus style).",
        "History Bowl: timed buzzer competition; team collaboration norms and roster sizes are in IHBB/IHO rules documents (not fully extracted here).",
        "Index team_size 4 matches common bowl roster practice but confirm in official rules PDF."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Buzzer interrupt timing and neg penalties are central and hard to simulate from static packets.",
        "Bee vs Bowl formats differ — benchmark excludes Bee/MS per collection notes."
      ]
    },

    "ioai_team": {
      "name": "International Olympiad in Artificial Intelligence — Team Challenge",
      "best_source_urls": [
        "https://ioai-official.org/wp-content/uploads/2026/06/IOAI2026-Contest-Rules-and-Tehnical-Appendix.pdf",
        "https://ioai-official.org/resources/"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team Challenge is an official IOAI component; national teams collaborate seated together.",
        "Style changes yearly (2024: AI creative tools; 2025: humanoid robots; 2026 style TBA at rules time).",
        "Number of computers and allowed websites/tools are task-specific, announced before the round.",
        "No communication with people outside the contest hall during Team Challenge.",
        "Approved/prohibited items similar to Individual Contest (phones/books/storage media generally prohibited in Individual rules).",
        "Duration: few hours to a full day depending on style; scoring task-specific; English tasks; translation site may be allowed as announced.",
        "Appeals via Team Leaders within organizer-specified windows."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Allowed-tool surface is intentionally year-specific — freeze the year’s task appendix.",
        "Physical robot tasks (2025-style) are non-comparable to pure software agents."
      ]
    },

    "science_olympiad": {
      "name": "Science Olympiad (USA)",
      "best_source_urls": [
        "https://www.soinc.org/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "National organization site; Divisions B/C teams capped at 15 students (standard national rule; exact wording in membership Rules Manual).",
        "Event-specific rules manuals are membership-locked — free sample exams only in this repo’s collection strategy.",
        "Many events allow specified binders/tools; others are build/lab — per-event PDFs required."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Without the locked Rules Manual, event-level tool lists cannot be asserted.",
        "15-person multi-event tournament ≠ one exam packet."
      ]
    },

    "wro": {
      "name": "World Robot Olympiad",
      "best_source_urls": [
        "https://wro-association.org/wp-content/uploads/WRO-2025-RoboMission-General-Rules.pdf",
        "https://wro-association.org/competition/2025-season/"
      ],
      "retrieved": true,
      "hard_constraints": [
        "RoboMission General Rules 2025: team of 2 or 3 students + coach; 1 student + coach is not a team; one category per student/team per season.",
        "Age groups Elementary/Junior/Senior with birth-year windows.",
        "Season publishes separate Game documents + Q&A that can extend/redefine rules; national organizers may adapt.",
        "Robot must solve field tasks under game timing/scoring tables (category-specific).",
        "Future Innovators / Future Engineers have their own General & Game Rules on the season page."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Physical robot construction, sensors, and table runs are outside software-agent fidelity.",
        "Always pair General Rules with the year’s Game PDF + Q&A."
      ]
    },

    "odyssey_of_the_mind": {
      "name": "Odyssey of the Mind",
      "best_source_urls": [
        "https://odysseyofthemind.com/program-guide/",
        "https://oklahomaom.com/wp-content/uploads/2026/02/2025-26-Program-Guide.pdf"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Teams of up to 7 members under an adult coach; recommend ≥5; all who contributed stay on roster.",
        "Long-Term problems solved over weeks/months; Spontaneous solved on-site; Style scoring component.",
        "Outside assistance restrictions are central (coaches may not contribute ideas to the solution — details in Program Guide).",
        "Full scoring packets / long-term specifics often membership-gated; public synopses only for many past problems."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Physical props, vehicles, structures, and live Spontaneous cannot be PDF-synopses-evaluated as equivalent.",
        "Outside-assistance edge cases need the full Program Guide sections."
      ]
    },

    "wmtc": {
      "name": "World Mathematics Team Championship",
      "best_source_urls": [
        "https://wmtc.international/",
        "https://wmtc.international/rules/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Homepage: teams of six historically; Individual + Team + Relay structure; 2026 announcement changes Individual to 2 rounds (20 min MC + 40 min short answer) with team contribution = sum/6 (max 70 from individuals).",
        "Team Round changed to require more teammate interaction (details promised on Rules page).",
        "Relay: 7 minutes × 3 rounds (2026 announcement).",
        "Dedicated Rules page fetch returned an embedded ‘WMTC Rules Test’ loader without extractable regulation text — treat detailed calculator/device bans as not retrieved."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Need the actual Rules document content (video/PDF behind the Rules page) for materials bans.",
        "Benchmark extracts Team Round only from mixed PDFs."
      ]
    },

    "fyziklani": {
      "name": "Physics Brawl Online (Fyziklání)",
      "best_source_urls": [
        "https://physicsbrawl.org/download/2025/rules-en-250901.pdf"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team size 1–5; 3-hour online contest via official environment.",
        "Internet and literature allowed; calculators and drafting supplies allowed.",
        "Generative AI strictly prohibited (ChatGPT-class tools) — disqualification risk.",
        "Communicate only with teammates or organizers (chat for wording/tech only); no teachers/other teams.",
        "Progressive series (Main + Hurry-up); numeric answers with specified sig figs/units; incorrect attempts reduce points and impose 1-minute series lockout; skips available after 90 minutes (≤10 skips, −1 point each).",
        "Keep solution materials for possible post-contest video-call verification."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Do not confuse with in-person Fyziklání (opposite: no internet / printed materials) — benchmark is Online.",
        "Live scoreboard hide final 20 minutes and fairness video calls are operational details."
      ]
    },

    "hmmt_guts": {
      "name": "HMMT Guts Round (February and November)",
      "best_source_urls": [
        "https://hmmt.co/www/tournaments/testing",
        "https://www.hmmt.org/www/tournaments/testing"
      ],
      "retrieved": true,
      "hard_constraints": [
        "No books, notes, calculators, or computational aids; no drawing aids (rulers/compasses/etc.); no laptops/PDAs/phones.",
        "Guts: 80 minutes; 36 short-answer questions in sets of 3 (November) or 4 (February); progressive runner submits a set then fetches the next.",
        "Team event — all members collaborate; grading immediate / live scoreboard.",
        "HMMT team sizes are tournament-registration-defined (commonly 6–8; confirm on registration pages for the year).",
        "Answers must follow official acceptable-answer PDF."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Progressive batch unlocking + runner logistics are the distinctive constraint.",
        "Exact roster min/max should be frozen from that tournament’s registration rules."
      ]
    },

    "purple_comet": {
      "name": "Purple Comet! Math Meet",
      "best_source_urls": [
        "https://purplecomet.org/rules",
        "https://purplecomet.org/faq"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team size 1–6; adult supervisor required; each team needs its own computer/Internet session (shared computers ⇒ sequential team starts).",
        "MS: 20 problems / 60 minutes; HS: 30 / 90 minutes within a multi-day window (244 hours stated for 2026).",
        "Teamwork encouraged; no help from non-members.",
        "Calculators and computation tools allowed (Desmos, WolframAlpha, Mathematica, GeoGebra, custom code, etc.) for calculations/diagrams only.",
        "May use local books/notes; may NOT use Internet to find solution methods/definitions instruction; may NOT use generative AI (ChatGPT/Gemini/Copilot/Claude etc.) to produce/explain/verify answers or code.",
        "Answers: non-negative integers via web form; last submission per problem counts; remote teammates may communicate."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Hardest policy to enforce for LLM agents: 'tools compute, humans choose methods' + AI ban.",
        "Supervisor integrity model has no agent analogue."
      ]
    },

    "qanta": {
      "name": "QANTA Quiz Bowl",
      "best_source_urls": [
        "https://www.qanta.org/"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "QANTA is a research quiz-bowl dataset/project; not a live tournament rulebook.",
        "Underlying quiz bowl norms (NAQT/ACF-style): 4 active players, tossup interruptible reading, bonuses to scoring team — take from the packet’s governing organization rules when simulating.",
        "Benchmark rows are question-level (eval_unit=question), not full matches."
      ],
      "confidence": "low",
      "proxy_limitations": [
        "Static tossup answering ≠ buzzer skill / neg risk / team nonverbal cues.",
        "No single official QANTA competition regulations PDF."
      ]
    },

    "science_bowl": {
      "name": "DOE Science Bowl",
      "best_source_urls": [
        "https://science.osti.gov/-/media/wdts/nsb/pdf/NSB-Resources/Rules2026.pdf",
        "https://science.osti.gov/wdts/nsb/Regional-Competitions/Resources"
      ],
      "retrieved": true,
      "hard_constraints": [
        "Team: 4 or 5 students; only 4 play at a time.",
        "Tossups (4 pts) + bonuses (10 pts); 5 seconds to buzz after tossup read; bonus 20 seconds team discussion (30s visual at Nationals).",
        "Halves: 8 minutes regional / 10 minutes National Finals; question begun before time is finished.",
        "On tossups: quiet nonverbal communication only among teammates; no audible verbal/mouthing/tapping; must buzz before answering.",
        "No unauthorized aids implied by oral buzzer format; coaches not part of answering.",
        "Benchmark is HS question-level subsample, not full timed matches."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Interrupt timing, blurt penalties, and double-interrupt scoring need an event engine.",
        "Question-level eval omits match strategy."
      ]
    },

    "mystery_hunt": {
      "name": "MIT Mystery Hunt",
      "best_source_urls": [
        "https://mitmh2026.com/",
        "https://puzzles.mit.edu/"
      ],
      "retrieved": true,
      "hard_constraints": [
        "No official maximum team size; 2026 FAQ: finish-oriented teams often need 30+ experienced solvers; designed for varied sizes.",
        "Weekend MLK hunt; kickoff Friday; remote play possible for most content, but in-person runaround required to win; ≥1 current MIT student required to win/write next year.",
        "Heavy within-team coordination; internet/tools generally unrestricted as a community puzzlehunt (not a closed-book exam) — year FAQ does not impose calculator/AI bans.",
        "Benchmark is question-level puzzle subsample with answers, not a full hunt."
      ],
      "confidence": "high",
      "proxy_limitations": [
        "Index team_size 12 is a modeling stub vs real 30–100+ teams.",
        "Physical runarounds, interactions, and meta structure are out of scope for isolated puzzle rows.",
        "Unrestricted web/tools make 'fair human comparison' poorly defined for LLM agents."
      ]
    },

    "nyu_ctf_bench": {
      "name": "NYU CTF Bench (CSAW)",
      "best_source_urls": [
        "https://github.com/NYU-LLM-CTF/NYU_CTF_Bench"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Benchmark packaging of CSAW CTF challenges for LLM agents — not CSAW’s live contest rulebook.",
        "Underlying CSAW CTF: Jeopardy-style flags; team collaboration on shared challenges; tooling unconstrained except fair-play / no attacking infra — confirm on year CSAW rules.",
        "Rows are challenge-level (eval_unit=question)."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Sandbox/tool access in the bench may differ from live CTF networks.",
        "Team size 5 in index is modeling, not an extracted CSAW hard cap from this crawl."
      ]
    },

    "cybench": {
      "name": "Cybench",
      "best_source_urls": [
        "https://github.com/andyzorigin/cybench"
      ],
      "retrieved": "partial",
      "hard_constraints": [
        "Research benchmark of professional CTF tasks for agent evaluation; constraints are benchmark harness rules, not a governing olympiad statute.",
        "Treat as benchmark_native: follow Cybench task metadata (timeouts, allowed tools) per challenge pack."
      ],
      "confidence": "medium",
      "proxy_limitations": [
        "Not designed as multi-human team olympiad rules.",
        "No single PDF 'regulations' — repository README/task specs are the source of truth."
      ]
    }
  }
}
```

---

## Cross-cutting notes for agent simulation

| Cluster | Typical hard bans | Typical collaboration | Highest-risk proxy gap |
|--------|-------------------|-----------------------|------------------------|
| Paper math/linguistics (IOL, ARML*, HMMT Guts, WMTC Team) | Calculators/electronics/internet | Free within team | Wall-clock + handwriting |
| Programming (ICPC, IIOT) | Internet (except judge); device limits; language limits | Share 1–2 machines | Keyboard contention |
| Open-resource with AI bans (Purple Comet, Physics Brawl Online) | Generative AI; (PC) method-search | Free within team | Enforcing AI/method bans on LLM agents |
| Open-resource with disclosure (IEO BC, CFA) | Outside humans; slide/report locks | Free within team | Oral defense + paid data |
| Lab / robot / cyber defense | Host kit only | Team | Physical/live systems |
| Oral rubric (Jessup, Vis, Ethics Bowls, WSC) | Outside assistance rules vary | Team | Live speaking rounds |
| Question-level corpora (QANTA, Science Bowl rows, Mystery Hunt rows, CTF benches) | Inherit parent sport if any | N/A | Not session-equivalent |

---

## Fetch failures / incomplete retrievals (explicit)

| URL / source | Status |
|--------------|--------|
| ARML Power Contest Rules page | Retrieved HTML: **“Under Construction”** |
| ARMLPower_Fall_2025_Administrivia.pdf | **Fetch timed out** |
| WMTC `/rules/` | Page loads embedded player; **no extractable rules text** |
| EOES Rules & Regulations PDFs (via documents page) | Hub retrieved; **PDF bodies not downloaded** |
| APPE / NHSEB full Rules PDFs | Hubs retrieved; **PDF click-throughs not fully extracted** |
| IChTo / Wharton / GCCH / PUMaC year packets | **Insufficient primary detail** |
| NCCDC handbook on ccdc.io | Redirect noted; **handbook not fetched** |
| Jessup FAQ URL from DATA_COLLECTION | Worked via `ilsa.org/jessup-competitors/jessup-faq/` (alternate path previously 404’d in one attempt) |

**Retraction (2026-08-12).** The `gcch_harvard` entry above cited `gcchatharvard.com`, a retired
domain, and conflated the university-level Global Case Competition at Harvard
(`thecasecompetition.org`) with the high-school Harvard Crimson Global Case Competition
(`casecomp.org`). The entry carries `superseded_by`, so the merge step skips it; the card takes its
facts from `docs/rules_lowconf_2026-08-12.md`.

---

## Provenance preference checklist (already in-repo)

Primary URLs already cited in Simulator Matrix / rule-card provenance that this crawl re-verified (retrieved successfully unless noted above):

- IOL `rules.pdf` + guidelines
- IEO Regulations + Syllabus PDFs
- IIOT Regulations.pdf + 2026 online rules
- ICPC WF programming environment + on-site registration + EUC 2026 rules
- Purple Comet `/rules`
- Physics Brawl Online rules PDF 2025-09-01
- IJSO Statutes Qatar 2019 PDF
- ARML competition rules page
- HMMT testing info
- Science Bowl Rules2026.pdf
- Jessup 2027 Official Rules PDF
- Vis 31st Rules PDF
- WRO 2025 RoboMission General Rules PDF
- Odyssey Program Guide
- IOAI 2026 Contest Rules PDF
- CFA Research Challenge Official Rules PDF

---

*End of crawl report.*
