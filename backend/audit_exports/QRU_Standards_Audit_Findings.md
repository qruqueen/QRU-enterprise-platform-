# QRU Factory — Standards Audit Findings Report

| Field | Value |
|---|---|
| Audit date | 2026-07-24 |
| Factory iteration | 94 |
| Total standards | 39 |
| Total lessons learned | 6 |
| Product recipes | 23 |
| Product Manufacturing Specifications (PMS) | 10 |
| Mode | READ-ONLY (no records created, renamed, connected, or modified) |

---

## A. Missing Dependency References
- **STD-EIP-0001** is referenced by **STD-EIP-0002** (`enterprise_architecture.py`) and **STD-RFN-0001** (`refinement_engine.py`) but **has no record, DOC_ID, seed, or alias** anywhere.
  - Classification: **Planned but never created** (forward reference; pillar map `learning_human_dev -> STD-EIP-0001`; "Sprint A" naming implies EIP-0001 was the intended foundation doc). Not renamed, superseded, or deleted.

## B. Governance-Graph Orphans (15)
Not referenced by literal STD-ID in code; most have a functional implementation under a different module name.

| ID | Name | Impl. component | Doc-only? | Likely parent | Confidence |
|---|---|---|---|---|---|
| STD-00017 | Agent Training Guide | workforce.py | Mostly doc | STD-00028/00006 | Med |
| STD-00018 | Standard Registry | qiks.py (this registry) | Implemented | STD-00005 | High |
| STD-00019 | Defense Portfolio Protection | — | Doc-only | STD-00024 | Med |
| STD-00020 | Methodology Manual | aggregates 00007/00010 | Doc-only | STD-00007 | Med |
| STD-00021 | Experience Design Architecture | design_intelligence.py | Partial | STD-00016 | Med |
| STD-00022 | Intelligence Governance Charter | autonomy/intelligence | Partial | STD-00005 | Low |
| STD-00023 | Intelligence Growth Index | analytics.py | Partial | STD-00022 | Med |
| STD-00024 | Ownership & Classification | — | Doc-only | STD-00005 | Med |
| STD-00025 | Product Assembly Blueprint | manufacturing_foundation.py | Partial | STD-MFG-0001 | Med |
| STD-00026 | Factory Operations Blueprint | factory_os.py | Partial | STD-MFG-0001 | Med |
| STD-00028 | Factory Agent Governance Manual | workforce.py | Partial | STD-00006 | Med |
| STD-00029 | Research Intelligence | — | Doc-only | STD-00008 | Low |
| STD-00031 | Factory Command Center Dashboard | factory_os.py | Implemented | STD-00026 | Med |
| STD-00032 | Visual Intelligence Studio | design_studio.py/visual_studio.py | Implemented | STD-00016 | High |
| STD-00033 | Media Intelligence Division | cinema_studio.py/media_division.py | Implemented | STD-00016 | High |

## C. Code-Equivalent But Unregistered Capabilities
| Capability (Founder name) | Implemented as (code) |
|---|---|
| QRU Evidence Engine™ | PMF / product manifest (manufacturing_foundation.build_manifest) + verification_engine |
| Governance Binding Layer™ | governance_binding.py ("MO-008") |
| Internal Knowledge Protection | Content Integrity Guard + Source Verification Gate™ (book_manufacturing) |
| Product Preservation Rule™ / Gold Master™ | immutable-original sealing + assemble_master_package (book_manufacturing) |
| Pre-Ship Gate™ | Final Release Gate (manufacturing_foundation / book_manufacturing) |
| Product Promise Validation™ | partial: content_integrity_check + Source Verification Gate™ + Pre-Review Inspection™ |
| Cover Communication Standard™ / Thumbnail Test | partial: design_studio/design_language cover legibility; thumbnail generation exists, no pass/fail test |
| Reading Experience Standard™ | partial: book_structure.py / rendering_engine.py |
| QRU Dependency Registry™ | partial: related_standards graph (no dedicated registry) |

## D. Founder-Approved Records NOT FOUND (as registered standards)
| Item | Status |
|---|---|
| STD-WRT-0001 / QRU Editorial & Writing Bible™ | Not registered; editorial workflow partially in code |
| STD-EDT-0001 / QRU Editorial Director Operating Manual™ | Not registered; no editorial-director role/manual |
| STD-SER-0001 | Not found anywhere |
| STD-AI-0001 | Not registered; AI usage implicit in ai_service.py |
| QRU Evidence Engine™ | Not registered (equivalent = PMF, see C) |
| QRU Dependency Registry™ | Not registered (partial = related_standards) |
| Governance Binding Layer™ | Not registered (code = governance_binding.py) |
| Reading Experience Standard™ | Not registered (partial in code) |
| Product Promise Validation™ | Not registered (partial in code) |
| Cover Communication Standard™ | Not registered (partial in code) |
| Thumbnail Test | Not registered (generation only, no test) |
| Internal Knowledge Protection | Not registered (code = Content Integrity Guard) |
| Product Preservation Rule™ / Gold Master™ | Not registered (code = immutable original + Master Package) |
| Pre-Ship Gate™ | Not registered (code = Final Release Gate) |

## E. Empty / Missing Metadata Fields
- All 39 standards are **v1.0 / Active**.
- Only these carry hierarchy metadata (standard_type / designation / inherits_from / implemented_by): **STD-00005, STD-00027, STD-00030, STD-UKR-0001**.
- The other **35** standards have those 4 fields **empty**.
- **`supersedes` is empty on all 39**; `alias` is empty on all except STD-00027 (STD-KR-0001) and STD-00030 (STD-KR-0002).

---
*Read-only audit. No governance records were created, renamed, connected, merged, superseded, or modified. Original JSON export preserved unchanged.*
