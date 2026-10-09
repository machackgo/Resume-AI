# Stage 4C-0 professional-domain research v1

Research date: 2026-09-29. This snapshot contains 30 verified public sources and 65 original normalized principles across the ten requested research areas. It is research input to curriculum design, not evidence that a professional dataset or model has passed its acceptance gates.

## Method and provenance

We searched separately for ATS behavior, resume writing, technical resumes, job interpretation, cover letters, application answers, outreach, truthful representation, current recruiting conventions, and accessibility. We preferred first-party ATS documentation, university career guidance, employer guidance, professional ethics, government application guidance and primary survey summaries. SEO resume sites, anonymous advice, private profiles, gated career libraries and copied example corpora were excluded.

Each source in `sources.jsonl` records its URL, publisher, verified date, publication/update date only when supported, scope, confidence, access mode, limitations, licensing disposition and associated principle IDs. Most pages were inspected through the public indexed page text returned by web search. Two were also successfully opened directly. Several direct opens were restricted or failed; these failures were not bypassed. Indexed text verification is not a claim that a complete live HTML archive was downloaded. The retained snapshot consists of our original notes, not copyrighted page bodies.

Requested research model/configuration: `gpt-6-astra`, reasoning `ultra`. The agent cannot independently observe its serving runtime identity; observed-model fields remain null. No inference-token billing telemetry is exposed for this research pass.

## Source quality and limits

The official Greenhouse and Lever sources support claims about their own parser behavior and fields, not a universal ATS algorithm. University advisers supply useful professional conventions but generally do not establish causal hiring effects. NACE's public 2026 survey summary supplies current early-career context; it is a respondent sample, not every employer or the senior AI labor market. The report does not repeat population-wide ATS adoption percentages or universal recruiter attention-span claims. W3C guidance concerns accessibility, which differs from resume parser performance. Government sources are explicitly scoped to their jurisdiction and application system.

`evidence_kind` separates source-supported advice, conservative inference, research-informed product rules and explicit user requirements contextualized by research. Hard truth requirements come from the user's product contract; research supports their professional rationale without pretending a career article defines a machine-grounding algorithm.

## A. ATS and resume parsing

A parsable resume requires explicit text and predictable field boundaries. Greenhouse documents failures involving images, complex layout, headers/footers and unclear sections; Lever exposes structured position and education fields. These are reasons to validate content structure and eventually extracted text. They do not justify claiming that a resume will pass all ATS products or assigning a universal ATS score. [Greenhouse parsing documentation](https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse), [Lever developer documentation](https://hire.lever.co/developer/documentation).

The conservative content default is conventional sections, consistent organization/title/date fields, ordered entries and supported skills. Do not change a true organization name by inventing a corporate suffix to satisfy a parser heuristic. File-size limits remain destination-specific.

## B. Professional resume writing

Prioritize relevant contributions; write precise actions and supported outcomes. A summary is optional as a curriculum design choice, not a universal rule established by the sources. Current versus completed work informs tense. Whole-document review should check redundancy, chronology and relevance. [MIT resume guidance](https://capd.mit.edu/resources/resumes/), [Princeton accomplishment statements](https://careerdevelopment.princeton.edu/advanced-degree-resume-guide/accomplishment-statements).

Numbers are useful when supported. Missing numbers should lead to a precise qualitative contribution, never an invented metric. [MIT resume toolkit](https://capd.mit.edu/resources/career-toolkit-crafting-an-effective-resume/).

## C. Technical and AI/ML resumes

Describe the system's purpose, the candidate's implementation contribution and relevant methods. Technical detail alone may not explain value; team contributions should show what the candidate actually did. Student projects are legitimate evidence but must remain labeled as projects. These principles generalize to AI/ML; no source establishes that every AI role requires one identical stack. [UT Austin technical bullets](https://careerservices.cns.utexas.edu/resources/resumes/strong-bullets-technical-resumes), [UT Austin technical careers](https://careerservices.cns.utexas.edu/explore-careers/career-guides-industry/technical-careers-guide).

LoRA versus QLoRA, API consumption versus construction, and study versus implementation remain product truth distinctions inherited from Stage 4A. They are not resume stylistic synonyms.

## D. Job-description interpretation

Preserve responsibilities, qualifications, preferences and conditions separately. Eligibility, work arrangement and relocation terms have different meanings. Keep exact numbers, operators and logical alternatives; a broad cloud preference does not name a provider. The no-inference requirement is a conservative product rule. [USAJOBS requirements](https://help.usajobs.gov/how-to/job-announcement/requirements), [eligibility versus qualifications](https://help.usajobs.gov/faq/application/eligibility/difference-from-qualifications), [announcement overview](https://help.usajobs.gov/how-to/job-announcement/overview), [UW position checklist](https://hr.uw.edu/comp/classified-staff/create-position-checklist/).

A small amount of public Microsoft posting structure was inspected, without copying postings into a corpus. Dynamic location aggregates are unsuitable as stable evaluation records without independent job identity and usage rights. [Microsoft technical role descriptions](https://careers.microsoft.com/v2/global/en/locations/hyderabad.html).

## E. Cover letters

Connect a few selected examples to the role in a concise narrative, with a clear purpose and professional closing. One page is a practical default, not a universal word limit. Company-specific details and personal motivations need actual supplied context. The letter should complement the resume. [MIT cover-letter guidance](https://capd.mit.edu/resources/how-to-write-an-effective-cover-letter/), [MIT cover-letter toolkit](https://capd.mit.edu/resources/career-toolkit-writing-a-cover-letter/).

## F. Application answers

Administrative facts and semantic selection questions need different treatment. Use concrete experience to answer the actual question and obey explicit length limits. STAR is useful for behavioral examples but unnecessary for a short factual answer. Exact fields belong to deterministic profile lookup. Missing preferences or sensitive factual information require user input. [Cambridge application forms](https://www.careers.cam.ac.uk/application-forms).

US disability and citizenship guidance demonstrates why these questions cannot be answered creatively. This curriculum does not decide an individual's legal status or a form's legality. [EEOC disability inquiries](https://www.eeoc.gov/pre-employment-inquiries-and-disability), [EEOC citizenship inquiries](https://www.eeoc.gov/pre-employment-inquiries-and-citizenship). Questionnaire claims must remain consistent with application evidence. [USAJOBS questionnaire guidance](https://help.usajobs.gov/how-to/job-announcement/how-to-apply).

## G. Professional outreach

Explain a real reason for contact, present limited relevant information and make a clear, proportionate request. Informational outreach and recruiter application messages have different purposes. Any referral, acquaintance, previous interaction or recipient authority requires supplied evidence. Discovery and sending are outside this research stage. [MIT informational interviews](https://capd.mit.edu/resources/conducting-informational-interviews/), [MIT networking guidance](https://capd.mit.edu/blog/2025/06/01/building-a-network-digital-and-in-person-strategies-for-students-recent-graduates-and-postdocs/).

## H. Truthfulness and grounding

Professional representation should be honest about qualifications. AI suggestions require fact-checking and confidentiality safeguards. Claim-to-evidence audit records and hard deterministic rejection are product implementations of this principle, not a claim that the sources specify those technical mechanisms. [ACM ethics code](https://www.acm.org/binaries/content/assets/about/acm-code-of-ethics-and-professional-conduct.pdf), [NACE AI ethics guidance](https://www.naceweb.org/career-development/organizational-structure/applying-naces-principles-for-ethical-professional-practice-to-ai).

## I. Current conventions

The 2026 NACE public summary supports demonstrating relevant skills through examples; it does not establish universal employer requirements. Employer match indicators do not guarantee selection. Instructions can change, including resume-length policies. [NACE 2026 survey summary](https://naceweb.org/research/reports/job-outlook/), [Microsoft hiring guidance](https://careers.microsoft.com/v2/global/en/hiring-tips), [current USAJOBS resume instructions](https://help.usajobs.gov/faq/application/documents/resume/what-to-include).

## J. Accessibility and document structure

Logical heading hierarchy and reading order support machine navigation. Correctly authored/tagged columns can be accessible; therefore single-column is a broad parser-compatibility default, not a universal accessibility requirement. JSON validity cannot establish that a future PDF has correct tags or that a DOCX works with assistive technology. The future File Generator must validate rendered artifacts separately. [W3C PDF reading order](https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF3), [W3C headings](https://www.w3.org/WAI/tutorials/page-structure/headings/).

## Conflicting guidance and conservative resolution

- **Length:** student one-page advice differs from advanced/experienced and academic use. Select by context; explicit destination instructions win. Current USAJOBS guidance caps federal resumes at two pages, so older unlimited-federal-resume conventions are not retained. [MIT 2026 student guidance](https://capd.mit.edu/blog/2026/06/23/interphase-2026-resume-resources/), [MIT CV comparison](https://capd.mit.edu/resources/cvs/).
- **Quantification:** some writing advice urges metrics or permits early drafting estimates. This product requires exact grounded values; a qualitative result is preferable when numbers are absent. No metric quota enters the rubric.
- **Technical detail:** specificity helps, but jargon can obscure meaning. Preserve exact technical entities while explaining purpose to the intended reader.
- **Layout:** accessibility permits correctly tagged complex layouts; some ATS parsers document them as risks. Default to simple ordered content, then test the actual renderer and destination.
- **AI authorship:** Harvard recommends AI mainly for editing and requires authentic review; the product's generation objective does not erase that caution. Targets must be grounded drafts with reviewable provenance and must honor employer AI restrictions. [Harvard AI guidance](https://careerservices.fas.harvard.edu/ai-resumes-and-cover-letters/).
- **Outreach:** an informational interview is not inherently a job request. Choose the message purpose from supplied context rather than applying one template everywhere.

## Research-to-curriculum handoff

The principles are ready to inform task schemas and frozen rubrics, subject to the main release audit. Truth, user constraints and explicit instructions take precedence over stylistic preferences. No public resume, private candidate record, long job posting, copyrighted sample, or unclear-license external dataset has been included in training data. No real-world job evaluation corpus has been released; only its safe future design is considered.

Remaining evidence limits: guidance is weighted toward US/UK early-career and university contexts; senior industry style choices need careful synthesis. There is no direct evidence here establishing an optimal dataset size, task ratio, number of teacher passes, model training order or sequence length. Those are later empirical curriculum-engineering decisions. This research alone cannot certify professional curriculum readiness for QLoRA.
