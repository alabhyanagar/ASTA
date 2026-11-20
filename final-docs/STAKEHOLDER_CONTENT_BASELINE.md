# ASTA Stakeholder Document Content Baseline

**Baseline ID:** ASTA-CONTENT-BASELINE-2026-11-20-02  
**Status:** Frozen for drafting as a stakeholder-review baseline; not product approval and not authorization to begin implementation.  
**Intended outputs:** Stakeholder-review PRD, SRS, and TAD in editable DOCX format.

## 1. Baseline purpose

This baseline resolves the source set and drafting rules for the three stakeholder documents. It freezes the **content to be represented**, not every product choice. Confirmed decisions remain distinguishable from recommendations, proposals, open questions, and historic examples.

## 2. Controlled sources

The itemized audit is in [`STAKEHOLDER_CONTENT_COVERAGE_LEDGER.md`](STAKEHOLDER_CONTENT_COVERAGE_LEDGER.md). The source hierarchy for drafting is:

1. Explicit decisions in the user project discussion.
2. Latest `final-docs/PRD.md`, `SRS.md`, and `TAD.md`, subject to restoring unique accepted features identified in the ledger.
3. Supporting `final-docs` documents and architecture diagrams.
4. Prior in-project `ASTA_Software_Requirements_Specification.docx`, other-machine `AI_Software_Testing_Platform_SRS.docx`, `machine_a_project_context.md`, original taxonomy images, and earlier architecture diagrams as feature/constraint inputs.
5. Root PRD/TAD drafts and master prompt files as historical/contextual inputs only. Prompt wording does not become a product decision by itself.

## 3. Confirmed content locked into the draft

- ASTA is a local-first installed testing product with an agent workflow; CLI-first, with optional MCP integration sharing the same application services.
- Users select multiple test types. ASTA does not blindly run every available type.
- Additional recommendations require explicit approval of the exact additions before execution.
- Each selected test domain gets an individual report and the run gets a consolidated report.
- Plans are reviewable before generation/execution by default; scope, approvals, risk gates, and runtime policy remain explicit.
- The evaluator is deterministic. AI is bounded/advisory and cannot set scope, authorization, evidence, evaluator policy, or authoritative pass/fail.
- White-box unit tests use the target language/runtime unless a declared adapter binding supports otherwise; black-box checks may use another supported language against an isolated target; component/integration checks declare white-box/black-box first.
- Preserve the requested adapter tiers exactly: Tier 1 Python (`pytest`, `Playwright`), TypeScript/JavaScript (`Vitest`, `Playwright`), Java (`JUnit 5`, `RestAssured`); Tier 2 C# (`xUnit`, `Playwright for .NET`), Go (`go test`, `Testify`), Kotlin, Swift, Dart, Ruby, PHP; Tier 3 Robot Framework (`.robot`), Gherkin (`.feature`), Karate DSL. These are desired support scope, not an assertion that they are available in M1.
- Preserve the proposed logical repository layout as a TAD appendix, explicitly marked illustrative and non-binding.
- Source modification is off by default. Application business logic is not automatically patched in the MVP. Any repair is bounded, reviewable, traceable, and cannot weaken assertions or hide failures.
- Network is denied by default; exact target/action/risk authorization, worker resource limits, cleanup, secret handling, and sandbox validation are essential safety constraints.
- Unsupported, blocked, not applicable, awaiting-authorization, skipped, inconclusive, error, and not-measured states must be visible; no claim beyond tested scope.
- M1/M2/M3/Later are the current phase labels. Old P0/P1/P2 tags must be crosswalked and not silently assumed to equal the current milestones.

## 4. Content requiring explicit stakeholder decision

The docs will visibly mark, not guess:

- ASTA full product-name expansion (Agent vs Platform).
- Whether bounded repair of generated tests/fixtures/config is M1 or later; the hard maximum of five attempts per run and recommended three per affected scenario remain in the requirement history unless stakeholders change them. App business logic stays outside MVP auto-patching.
- Whether natural-language scope selection ships in M1 or a later phase.
- When the accepted CI runner/integration first ships and which CI provider is supported.
- Exact operating systems, package/installer format (including `.exe`), first language/framework matrix, sandbox runtime and proof, model/provider, DB/storage/secret store, API endpoints/auth, tool versions/licenses, severity scale, retry policy, numeric quality/resource/performance targets, retention/deletion/backup rules, benchmark gates, and product version numbers/dates.
- Any numerical values found in old samples (e.g. `max_context_tokens: 12000`, timeout `300`, retries `3`, line coverage `70`, branch coverage `60`, mutation enabled) are examples, not approved defaults.
- The exact OS/runtime/framework availability within the requested adapter tiers, first-release adapter set, and support dates remain open. Earlier manual/recommended/custom selection modes are presented as a proposed interaction pattern; multi-select and explicit approval remain the confirmed product rules.

## 5. Standard and document rules

- SRS structure and requirements writing are guided by ISO/IEC/IEEE 29148:2018; do not claim formal compliance.
- TAD organization is guided by ISO/IEC/IEEE 42010:2022 architecture-description concepts.
- NFR coverage is reviewed against ISO/IEC 25010:2023 quality characteristics; numeric criteria remain stakeholder-approved, measurable values or `TBD`.
- Each DOCX front page says `Stakeholder Review Draft`, with version, issue date, document owner/preparer to be approved, approval names/status blank, and revision history.
- Preserve complete content. Use concise executive summaries for navigation only; do not replace requirements, taxonomy, edge cases, data/state rules, constraints, or open decisions with summaries.
- Cross-reference all requirement IDs, decision IDs, figures, tables, and source ledger rows. Preserve exact formulas and enum spelling.

## 6. Baseline freeze and change control

Revision 02 extends the initial freeze to include the full conversation's requested language/framework tiers and proposed repository layout, and records the selection-mode interaction as a proposal. This content baseline is frozen for the current DOCX drafting pass. It is not a final stakeholder sign-off. If a stakeholder later changes a locked choice or resolves an open decision, record the decision and update the affected PRD/SRS/TAD plus traceability. Do not silently edit this baseline; create a new baseline ID and change summary.

