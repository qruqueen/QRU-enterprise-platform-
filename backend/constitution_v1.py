"""QRU Factory™ Constitution (QRU-CON-0001) — Version 1.0, Founder Approved.

The supreme, version-controlled foundational governing standard. Stored VERBATIM (Knowledge-First:
never AI-generated or paraphrased). Bound to agents, pipelines, quality gates and the operating
experience. Future amendments create a NEW version + revision record — the approved v1.0 is never
silently overwritten (per §14).
"""
from database import db
from models import gen_id, now_iso, clean
import qiks

DOC_ID = "QRU-CON-0001"
VERSION = "1.0"
STATUS = "Founder Approved"
AUTHORITY = "Foundational"
EFFECTIVE = "2026-07"

# Structured sections (title + verbatim body). The full text is preserved in FULL_TEXT.
SECTIONS = [
    {"n": "1", "title": "The QRU Factory™ Mission",
     "summary": "A governed civilization of specialized intelligences that manufactures understanding and transforms it into meaningful human experiences."},
    {"n": "2", "title": "The QRU Craftsmanship Principle™",
     "summary": "Every product must be accurate enough to trust, understandable enough to use, beautiful enough to treasure, and meaningful enough to share (Trust · Understanding · Beauty · Impact)."},
    {"n": "3", "title": "The Four Civilizations of QRU™",
     "summary": "Knowledge, Creation, Design, and Legacy Civilizations — each with defined responsibilities and a primary output."},
    {"n": "4", "title": "The Universal QRU Flow™",
     "summary": "Question → Knowledge-Gap Check → Research → Verification → Understanding → Governed KR → Product → Creation → Design → QA → Approval → Vault → Distribution → Experience → Measurement → Legacy."},
    {"n": "5", "title": "The Treasure Standard™",
     "summary": "Three foundational tests every major output must pass: Understanding, Craftsmanship, Legacy. Fail any one → return for revision."},
    {"n": "6", "title": "The QRU Art-Direction Standard™",
     "summary": "Design stages understanding. Required design reasoning, the Hero Principle™, cinematic composition, material language, typography hierarchy, color foundation, the Three-Second Test, and the Design Critic requirement. Purple+gold+logo alone is NOT compliance."},
    {"n": "7", "title": "The QRU Operating Experience™",
     "summary": "Organize around the user's intended outcome. Primary question: 'What would you like to create today?' The interface must always answer where am I, what am I creating, which knowledge, what's done, what's next, what needs approval."},
    {"n": "8", "title": "The Factory Concierge™ Principle",
     "summary": "A human-facing guide that translates an intended outcome into the correct governed manufacturing workflow. The user manages the outcome; the Factory manages the specialized agents."},
    {"n": "9", "title": "Governance, Human Authority, and Automation",
     "summary": "AI serves the mission; governance protects it; people remain the reason. Approval modes: Human Approval Required (default), Auto-Select for Draft Preview Only, Governed Auto-Select (disabled until authorized)."},
    {"n": "10", "title": "Quality, Preservation, and Gold Master Certification™",
     "summary": "Four separate quality gates (Knowledge/Content, Technical, Design/Brand, Licensing/Rights). Product status ladder. Gold Master Certified™ is a controlled state assigned only by an authorized authority."},
    {"n": "11", "title": "The Master Asset Vault™ and Single Source of Truth",
     "summary": "Every approved asset has a traceable home. The interface must distinguish the Knowledge Record from products, supporting assets, and final distribution files."},
    {"n": "12", "title": "The QRU Decision Filter™",
     "summary": "Ten questions to ask before approving any new feature, workflow, agent, product, or partnership. Capability that makes the Factory harder to understand must be redesigned."},
    {"n": "13", "title": "The QRU Founder Promise™",
     "summary": "We will not sacrifice trust for speed, understanding for information, craftsmanship for convenience, or people for automation."},
    {"n": "14", "title": "Implementation Directive to Emergent",
     "summary": "Binding governing reference. Standards Registry, Governance Binding, Design Intelligence binding, UX binding, Knowledge-Gap routing, Product Relationship clarity, Production Continuity, and the Acceptance requirement (must govern behavior, not just labels)."},
]

# Product statuses (Constitution §10). Ordered idea → superseded.
PRODUCT_STATUSES = [
    "Idea", "Research Required", "Knowledge Record in Development", "Draft", "In Review",
    "Technical QA Passed", "Content and Brand QA Passed", "Distribution Ready",
    "Gold Master Certified™", "Published", "Archived", "Superseded",
]

# The four separate quality gates (§10).
QUALITY_GATES = [
    {"gate": "Knowledge and Content QA", "verifies": ["factual accuracy", "source quality", "uncertainty language",
                                                      "audience suitability", "understandable explanations", "claim integrity", "KR alignment"]},
    {"gate": "Technical QA", "verifies": ["file integrity", "dimensions/resolution", "playback/opening", "audio presence",
                                          "caption rendering", "encoding", "missing assets", "compatibility", "export readiness"]},
    {"gate": "Design and Brand QA", "verifies": ["QRU identity", "visual hierarchy", "composition", "typography",
                                                 "accessibility", "emotional impact", "representation", "art-direction compliance",
                                                 "product-family consistency", "no generic-template appearance"]},
    {"gate": "Licensing and Rights QA", "verifies": ["provider", "asset ID", "creator", "source reference", "license type",
                                                     "commercial-use permissions", "modification permissions", "attribution",
                                                     "acquisition date", "checksum", "evidence preservation"]},
]

# Approved automation modes (§9) — matches MO-012 behavior.
AUTOMATION_MODES = [
    {"mode": "Human Approval Required", "default": True,
     "rule": "No final manufacturing or distribution occurs until required human reviews are complete."},
    {"mode": "Auto-Select for Draft Preview Only", "default": False,
     "rule": "Temporary selections + a clearly-marked draft. Never Gold Master, final, publication-ready or distribution-approved."},
    {"mode": "Governed Auto-Select", "default": False,
     "rule": "Automate qualified decisions only with documented rules, sufficient approval history, validated scoring, monitored exceptions, and Founder authorization. Disabled by default."},
]

FULL_TEXT = """QRU FACTORY\u2122 CONSTITUTION \u2014 Version 1.0 (Founder Approved)
Document ID: QRU-CON-0001 \u00b7 Authority: Foundational \u00b7 Owner: QRU / Queen Rothswell Universe\u2122

1. THE QRU FACTORY\u2122 MISSION
QRU Factory\u2122 is a governed civilization of specialized intelligences working together to manufacture understanding and transform it into meaningful human experiences. It exists to receive meaningful questions; research available knowledge; evaluate and verify sources; identify uncertainty and conflicting evidence; translate complexity into understandable language; transform understanding into thoughtfully designed products; preserve the resulting intellectual and creative assets; and help those assets reach the people they were created to serve.

2. THE QRU CRAFTSMANSHIP PRINCIPLE\u2122
Every QRU product must be accurate enough to trust, understandable enough to use, beautiful enough to treasure, and meaningful enough to share. Four inseparable dimensions: Trust, Understanding, Beauty, Impact. No product is complete merely because a file was generated.

3. THE FOUR CIVILIZATIONS OF QRU\u2122
3.1 Knowledge Civilization\u2122 \u2014 discover, evaluate, verify, and manufacture trustworthy understanding. Output: a governed QRU Knowledge Record\u2122. When an approved KR does not exist, the Factory must not pretend it does; it must say so and offer to initiate the Knowledge Manufacturing Pipeline.
3.2 Creation Civilization\u2122 \u2014 transform understanding into useful products (books, workbooks, posters, knowledge cards, presentations, assessments, courses, teacher guides, videos, podcasts, audiobooks, social assets, interactive experiences, bundles). May express the same verified truth in different forms but must not silently change the underlying truth.
3.3 Design Civilization\u2122 \u2014 transform understanding into compelling, accessible, memorable experiences. Design is not decoration.
3.4 Legacy Civilization\u2122 \u2014 help trustworthy understanding travel, remain accessible, and create lasting impact (publishing, distribution, branding, licensing, analytics, version preservation, archival, IP stewardship).

4. THE UNIVERSAL QRU FLOW\u2122
Question \u2192 Knowledge-Gap Check \u2192 Research \u2192 Source Evaluation \u2192 Verification \u2192 Understanding \u2192 Governed Knowledge Record \u2192 Product Selection \u2192 Creation \u2192 Design and Art Direction \u2192 Technical Quality Review \u2192 Content and Brand Review \u2192 Human Approval Where Required \u2192 Master Asset Vault\u2122 \u2192 Distribution \u2192 Human Experience \u2192 Measurement \u2192 Reflection and Improvement \u2192 Legacy. The interface may simplify this; the governance behind it must remain intact.

5. THE TREASURE STANDARD\u2122
Understanding Test, Craftsmanship Test, Legacy Test. A product that fails any one must return for revision.

6. THE QRU ART-DIRECTION STANDARD\u2122
QRU does not decorate knowledge; QRU stages understanding. Required design reasoning (audience, purpose, first feeling, first notice, single visual hero, story, next action, supporting vs distracting elements, QRU distinction). The Hero Principle\u2122; cinematic composition; material language; typography hierarchy; QRU color foundation (Royal Purple #35106A, QRU Gold #F5B21A, Deep Navy #1F1840, White #FFFFFF); the Three-Second Design Test; the Design Critic requirement. Correct colors, logo, or a clean template alone do NOT constitute QRU design compliance.

7. THE QRU OPERATING EXPERIENCE\u2122
Organize around the user's intended outcome, not internal departments. Primary question: \u201cWhat would you like to create today?\u201d Users should not need to understand agent names, pipeline architecture, asset databases, checksums, or provider systems to create a product. At every important stage the interface should make clear: where am I, what am I creating, which knowledge is used, what is complete, what is happening, where it is stored, what needs approval, what happens next, and how to edit/export/publish.

8. THE FACTORY CONCIERGE\u2122 PRINCIPLE
The Factory Concierge\u2122 translates the user's intended outcome into the correct governed manufacturing workflow. The user manages the outcome; the Factory manages the specialized agents.

9. GOVERNANCE, HUMAN AUTHORITY, AND AUTOMATION
AI serves the mission. Governance protects the mission. People remain the reason for the mission. Human approval required for factual uncertainty, sensitive subjects, cultural representation, financial/health claims, final brand approval, licensing, public distribution, Gold Master certification, major KR changes, replacement of locked/approved assets. Approved automation modes: Human Approval Required (default), Auto-Select for Draft Preview Only, Governed Auto-Select (disabled until authorized).

10. QUALITY, PRESERVATION, AND GOLD MASTER CERTIFICATION\u2122
Separate gates: Knowledge and Content QA; Technical QA; Design and Brand QA; Licensing and Rights QA. Product statuses: Idea, Research Required, Knowledge Record in Development, Draft, In Review, Technical QA Passed, Content and Brand QA Passed, Distribution Ready, Gold Master Certified\u2122, Published, Archived, Superseded. Gold Master Certified\u2122 is a controlled approval state assigned only by an authorized user or governed approval authority.

11. THE MASTER ASSET VAULT\u2122 AND SINGLE SOURCE OF TRUTH
Every approved QRU asset must have a traceable home preserving IDs, KR relationship, versions, approvals, source/final files, agent history, selected/rejected assets, licensing evidence, checksums, QA reports, publication records, revision history, superseded versions, and distribution locations. A poster generated from a KR must not masquerade as, replace, or become the only visible representation of the KR. The interface must distinguish the Knowledge Record, products manufactured from it, supporting assets, and final distribution files.

12. THE QRU DECISION FILTER\u2122
Ten questions before approving any new feature/workflow/agent/product/partnership. A feature that adds capability but makes the Factory materially harder to understand must be redesigned before being considered complete.

13. THE QRU FOUNDER PROMISE\u2122
We will not sacrifice trust for speed, understanding for information, craftsmanship for convenience, or people for automation. Research before claiming; verify before certifying; simplify without distorting; design with intention; preserve what matters; keep learning from the people we serve.

14. IMPLEMENTATION DIRECTIVE TO EMERGENT
Binding governing reference. (A) Standards Registry: register as QRU-CON-0001, QRU Factory\u2122 Constitution, v1.0, Founder Approved, Foundational. (B) Governance Binding: bind applicable agents, pipelines, templates, quality gates, product workflows to the governing section. (C) Design Intelligence Binding: Section 6 as an active decision framework. (D) User-Experience Binding: move toward \u201cWhat would you like to create today?\u201d and guide from intention \u2192 knowledge \u2192 manufacture \u2192 approval \u2192 vault \u2192 publish. (E) Knowledge-Gap Routing: offer governed knowledge manufacturing when no approved KR exists. (F) Product Relationship Clarity: every product screen shows source KR, derived product, status, storage, approval history, next action, publishing options. (G) Production Continuity: Review \u2192 Edit \u2192 Approve \u2192 Vault \u2192 Export \u2192 Publish \u2192 Measure; finished assets must not become stranded. (H) Acceptance: concepts must actively govern behavior, not merely appear as labels. Preserve v1.0 unchanged; amendments create a new version and revision record.

REVISION RECORD
| 1.0 | July 2026 | Founder Approved | Initial QRU Factory\u2122 Constitution. |
"""


async def seed_constitution_v1():
    """Register QRU-CON-0001 verbatim (idempotent) in the dedicated collection + QIKS Standards Registry."""
    existing = await db.factory_constitution.find_one({"doc_id": DOC_ID, "version": VERSION})
    if not existing:
        await db.factory_constitution.insert_one({
            "id": gen_id(), "doc_id": DOC_ID, "name": "QRU Factory\u2122 Constitution", "version": VERSION,
            "status": STATUS, "authority_level": AUTHORITY, "effective_date": EFFECTIVE,
            "owner": "QRU / Queen Rothswell Universe\u2122", "read_only": True,
            "sections": SECTIONS, "full_text": FULL_TEXT, "word_count": len(FULL_TEXT.split()),
            "product_statuses": PRODUCT_STATUSES, "quality_gates": QUALITY_GATES, "automation_modes": AUTOMATION_MODES,
            "revision_record": [{"version": VERSION, "date": EFFECTIVE, "status": STATUS,
                                 "description": "Initial QRU Factory\u2122 Constitution establishing mission, civilizations, "
                                                "craftsmanship, art direction, operating experience, governance, quality, "
                                                "preservation, and implementation requirements."}],
            "created_at": now_iso(), "updated_at": now_iso(),
        })
    # Register in the QIKS Standards Registry so governance-binding can resolve constitutional references.
    if not await qiks.STD_COL.find_one({"id": DOC_ID}):
        await qiks.STD_COL.insert_one({
            "id": DOC_ID, "standard_id": DOC_ID, "name": "QRU Factory\u2122 Constitution",
            "category": "Enterprise Standards\u2122",
            "description": "The supreme, version-controlled foundational governing standard of the QRU Factory\u2122 "
                           "(mission, four civilizations, craftsmanship, art direction, operating experience, "
                           "governance, quality, preservation, decision filter).",
            "purpose": "Provide a single protected authority binding every agent, workflow, interface, quality gate, "
                       "and manufacturing pipeline to the QRU mission and values.",
            "status": "Active", "version": VERSION, "date_adopted": "2026-07", "founder_approval": True,
            "authority_level": AUTHORITY, "is_founder_document": True,
            "document_content": FULL_TEXT, "word_count": len(FULL_TEXT.split()),
            "source_document": "QRU-CON-0001 (Founder pasted, verbatim)", "classification": "Foundational Governance Standard",
            "related_standards": ["STD-00001", "STD-00005", "STD-00003", "STD-00016"],
            "implementation_status": "Implemented", "promotion_stage": "Institutional Knowledge\u2122",
            "change_history": [{"version": VERSION, "date": "2026-07",
                                "reason": "Adopted verbatim as the founder-approved QRU Factory\u2122 Constitution.",
                                "reviewer": "Founder", "founder_approval": True}],
            "superseded_versions": [], "created_at": now_iso(), "updated_at": now_iso(),
        })


async def get_constitution_v1():
    return clean(await db.factory_constitution.find_one({"doc_id": DOC_ID, "status": STATUS}))


async def get_section(n):
    doc = await get_constitution_v1()
    if not doc:
        return None
    return next((s for s in doc["sections"] if s["n"] == str(n)), None)
