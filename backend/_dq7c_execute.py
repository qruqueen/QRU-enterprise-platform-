"""DQ-7C Controlled Standards Metadata Execution (preview DB).
Additive-only, guarded, reversible. Set EXECUTE=1 env to write; default is DRY-RUN.
Honors all Founder stop conditions.
"""
import os, json, sys, datetime, asyncio
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
from motor.motor_asyncio import AsyncIOMotorClient

EXECUTE = os.environ.get('EXECUTE') == '1'
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
AUDIT = '/app/memory/audit'

# ---- Approved classification sets (DQ-7 / DQ-7B) ----
INH = {  # INHERITED_ENFORCED -> Manufacturing Promise pillar
    'STD-00001': 'MANUFACTURING_PROMISE.treasure_standard',
    'STD-00005': 'MANUFACTURING_PROMISE.constitutional_governance',
    'QRU-CON-0001': 'MANUFACTURING_PROMISE.constitutional_governance',
    'STD-00008': 'MANUFACTURING_PROMISE.verified_knowledge',
    'STD-00009': 'MANUFACTURING_PROMISE.enterprise_memory',
    'STD-00027': 'MANUFACTURING_PROMISE.verified_knowledge',
    'STD-00030': 'MANUFACTURING_PROMISE.verified_knowledge',
    'STD-UKR-0001': 'MANUFACTURING_PROMISE.verified_knowledge',
    'STD-RFN-0001': 'MANUFACTURING_PROMISE.continuous_craftsmanship',
}
GATE = {  # GATE_ENFORCED -> named gate
    'QRU-CON-0002': 'rendering_engine/deliverable_renderer:Publication Quality Standard\u2122',
    'STD-MFG-0001': 'manufacturing_flow:Universal Manufacturing Flow gate',
}
EVIDENCE_BACKED = set(INH) | set(GATE)  # 11
# owner + verification_status to add to the 5 constitutional-tier canonical records (where absent)
CONST5 = {
    'QRU-CON-0001': {'owner': 'QRU', 'verification_status': 'Verified'},
    'QRU-CON-0002': {'owner': 'QRU Press\u2122', 'verification_status': 'Verified'},
    'STD-MFG-0001': {'owner': 'QRU', 'verification_status': 'Verified'},
    'STD-EIP-0002': {'owner': 'QRU', 'verification_status': 'Verified'},
    'STD-RFN-0001': {'owner': 'QRU', 'verification_status': 'Verified'},
}
DQ7_FIELDS = ['lifecycle_status', 'enforcement_condition', 'enforcement_binding', 'dq7_prepared_at', 'dq7_evidence']
DQ7B_QIKS_FIELDS = ['owner', 'verification_status', 'dq7b_canonicalized_at']
DQ7B_PROJ_FIELDS = ['canonical_ref', 'projection', 'dq7b_indexed_at']


def stop(msg):
    print('\n\u26d4 STOP CONDITION TRIGGERED:', msg)
    sys.exit(2)


def additive_set(doc, field, value, changes, key):
    """Return update value only if field absent; if present-and-equal -> idempotent skip;
    if present-and-different -> STOP (would overwrite)."""
    if field in doc and doc.get(field) not in (None, '', []):
        if doc.get(field) == value:
            return None  # idempotent, already set
        stop(f"overwrite blocked: {key}.{field} exists='{doc.get(field)}' != new='{value}'")
    changes.setdefault(key, {})[field] = value
    return value


async def main():
    db = AsyncIOMotorClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]

    # ---------- STEP 1: pre-image snapshots ----------
    qiks = [d async for d in db.qiks_standards.find({})]
    cons = [d async for d in db.constitutional_registry.find({})]
    pre_q = json.loads(json.dumps(qiks, default=str))
    pre_c = json.loads(json.dumps(cons, default=str))
    if EXECUTE:
        json.dump(pre_q, open(f'{AUDIT}/dq7c_preimage_qiks.json', 'w'), indent=1)
        json.dump(pre_c, open(f'{AUDIT}/dq7c_preimage_constitutional.json', 'w'), indent=1)
    n_q, n_c = len(qiks), len(cons)
    print(f"STEP1 pre-image: qiks_standards={n_q} constitutional_registry={n_c}")
    if n_q != 39:
        stop(f"expected 39 qiks_standards, found {n_q}")
    if n_c != 5:
        stop(f"expected 5 constitutional_registry, found {n_c}")

    qkey = lambda d: d.get('standard_id') or d.get('id')

    # ---------- STEP 2: compute dry-run + guards ----------
    changes = {}
    by_class = {'INHERITED_ENFORCED': 0, 'GATE_ENFORCED': 0, 'FOUNDER_DECISION_REQUIRED': 0}
    for d in qiks:
        sid = qkey(d)
        additive_set(d, 'lifecycle_status', 'ADOPTED', changes, f'qiks:{sid}')
        if sid in INH:
            cls, binding = 'INHERITED_ENFORCED', INH[sid]
        elif sid in GATE:
            cls, binding = 'GATE_ENFORCED', GATE[sid]
        else:
            cls, binding = 'FOUNDER_DECISION_REQUIRED', None
        by_class[cls] += 1
        additive_set(d, 'enforcement_condition', cls, changes, f'qiks:{sid}')
        additive_set(d, 'enforcement_binding', binding, changes, f'qiks:{sid}')
        additive_set(d, 'dq7_prepared_at', NOW, changes, f'qiks:{sid}')
        additive_set(d, 'dq7_evidence', ('evidence-backed' if sid in EVIDENCE_BACKED else 'unsupported->FOUNDER_DECISION_REQUIRED'), changes, f'qiks:{sid}')
        # DQ-7B owner/verification for the 5 constitutional-tier canonical records (where absent)
        if sid in CONST5:
            additive_set(d, 'owner', CONST5[sid]['owner'], changes, f'qiks:{sid}')
            additive_set(d, 'verification_status', CONST5[sid]['verification_status'], changes, f'qiks:{sid}')
            additive_set(d, 'dq7b_canonicalized_at', NOW, changes, f'qiks:{sid}')

    # projection updates + canonical_ref resolution guard
    proj_resolution = {}
    for d in cons:
        cid = d.get('id')
        # canonical_ref must resolve to exactly one qiks standard_id
        matches = [x for x in qiks if qkey(x) == cid]
        if len(matches) != 1:
            stop(f"canonical_ref for {cid} resolves to {len(matches)} canonical records (must be exactly 1)")
        proj_resolution[cid] = qkey(matches[0])
        additive_set(d, 'canonical_ref', cid, changes, f'cons:{cid}')
        additive_set(d, 'projection', True, changes, f'cons:{cid}')
        additive_set(d, 'dq7b_indexed_at', NOW, changes, f'cons:{cid}')

    print("\nSTEP2 DRY-RUN")
    print(f"  documents affected: qiks={sum(1 for k in changes if k.startswith('qiks:'))}, cons={sum(1 for k in changes if k.startswith('cons:'))}")
    print(f"  enforcement classification counts: {by_class} (sum={sum(by_class.values())})")
    print(f"  fields added per qiks record: {DQ7_FIELDS} (+{DQ7B_QIKS_FIELDS} for the 5 constitutional-tier)")
    print(f"  fields added per constitutional_registry record: {DQ7B_PROJ_FIELDS}")
    total_writes = sum(len(v) for v in changes.values())
    print(f"  total additive field-writes: {total_writes} | overwrites: 0 | deletes: 0 | renames: 0")
    print(f"  canonical_ref resolution (each -> exactly 1): {proj_resolution}")
    # guard: evidence-backed must be exactly 11
    if by_class['INHERITED_ENFORCED'] + by_class['GATE_ENFORCED'] != 11:
        stop("evidence-backed count != 11")
    if by_class['FOUNDER_DECISION_REQUIRED'] != 28:
        stop(f"FOUNDER_DECISION_REQUIRED count != 28 (got {by_class['FOUNDER_DECISION_REQUIRED']})")

    if not EXECUTE:
        print("\n(DRY-RUN only — no writes. Set EXECUTE=1 to apply.)")
        return

    # ---------- STEP 3-5: execute writes ----------
    for key, fields in changes.items():
        coll, ident = key.split(':', 1)
        if coll == 'qiks':
            await db.qiks_standards.update_one({'standard_id': ident} if await db.qiks_standards.find_one({'standard_id': ident}) else {'id': ident}, {'$set': fields})
        else:
            await db.constitutional_registry.update_one({'id': ident}, {'$set': fields})
    print("\nSTEP3-5 writes applied.")

    # ---------- STEP 6-8: verification ----------
    post_q = [d async for d in db.qiks_standards.find({})]
    post_c = [d async for d in db.constitutional_registry.find({})]
    if len(post_q) != n_q or len(post_c) != n_c:
        stop("record counts changed after write")
    # projection resolution
    for d in post_c:
        matches = [x for x in post_q if (x.get('standard_id') or x.get('id')) == d.get('canonical_ref')]
        if len(matches) != 1:
            stop(f"post-check: canonical_ref {d.get('canonical_ref')} resolves to {len(matches)}")
    # governance metadata intact (spot-check preservation vs pre-image)
    preq_by = {(x.get('standard_id') or x.get('id')): x for x in pre_q}
    intact = True
    for d in post_q:
        sid = d.get('standard_id') or d.get('id')
        p = preq_by.get(sid, {})
        for f in ['founder_approval', 'related_standards', 'authority_level', 'classification', 'promotion_stage', 'document_content', 'name', 'id', 'version', 'category']:
            if f in p and p.get(f) != json.loads(json.dumps(d.get(f), default=str)):
                intact = False
                print(f"  \u26a0 changed pre-existing field {sid}.{f}")
    print(f"STEP6-8 verification: counts stable ({len(post_q)}/{len(post_c)}), projections resolve 1:1, governance metadata intact={intact}")

    # ---------- STEP 9: evidence report + rollback manifest ----------
    report = {
        'executed_at': NOW, 'scope': 'PREVIEW database', 'qiks_count': len(post_q), 'cons_count': len(post_c),
        'enforcement_counts': by_class, 'total_field_writes': total_writes,
        'overwrites': 0, 'deletes': 0, 'renames': 0,
        'canonical_ref_resolution': proj_resolution, 'governance_metadata_intact': intact,
        'evidence_backed_ids': sorted(EVIDENCE_BACKED),
    }
    json.dump(report, open(f'{AUDIT}/dq7c_post_execution_report.json', 'w'), indent=1)
    rollback = {
        'method': 'additive-only reversal',
        'qiks_unset_fields': DQ7_FIELDS + DQ7B_QIKS_FIELDS,
        'note_owner_verification': 'unset owner/verification_status ONLY on the 5 CONST5 ids (added by DQ-7C); pre-image confirms they were absent pre-run',
        'cons_unset_fields': DQ7B_PROJ_FIELDS,
        'preimage_files': ['dq7c_preimage_qiks.json', 'dq7c_preimage_constitutional.json'],
        'const5_ids': sorted(CONST5),
    }
    json.dump(rollback, open(f'{AUDIT}/dq7c_rollback_manifest.json', 'w'), indent=1)
    print("STEP9 report + rollback manifest written.")

asyncio.run(main())
