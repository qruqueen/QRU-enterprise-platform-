"""READ-ONLY registry reconciliation harvester. Prints structured JSON for the Master Ledger.
Does not write to any QRU collection or file."""
from dotenv import load_dotenv; load_dotenv('/app/backend/.env')
import asyncio, os, re, json, glob
from motor.motor_asyncio import AsyncIOMotorClient

BACKEND = '/app/backend'
FRONTEND = '/app/frontend/src'


def read(p):
    try:
        return open(p, encoding='utf-8', errors='ignore').read()
    except Exception:
        return ''


async def main():
    db = AsyncIOMotorClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
    out = {}

    # ---- backend routers + server registration ----
    server = read(f'{BACKEND}/server.py')
    routers = sorted(os.path.basename(p)[:-3] for p in glob.glob(f'{BACKEND}/routers/*.py') if not p.endswith('__init__.py'))
    registered = re.findall(r'from routers\.(\w+) import', server)
    included = re.findall(r'(\w+)_router,', server)
    out['routers'] = {'files': routers, 'imported': sorted(set(registered)),
                      'not_imported': sorted(set(routers) - set(registered))}

    # ---- API route prefixes across all routers ----
    prefixes = []
    for r in routers:
        txt = read(f'{BACKEND}/routers/{r}.py')
        for m in re.findall(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']+)', txt):
            prefixes.append((r, m))
    out['api_prefixes'] = sorted(set(prefixes))

    # ---- frontend routes (App.js) + page files ----
    appjs = read(f'{FRONTEND}/App.js')
    fe_routes = re.findall(r'<Route\s+path="([^"]*)"\s+element=\{<(\w+)', appjs)
    imports = dict(re.findall(r'import\s+(\w+)\s+from\s+"@/pages/([\w/]+)"', appjs))
    pages = {os.path.basename(p)[:-3] for p in glob.glob(f'{FRONTEND}/pages/*.js')}
    missing_page_import = [(path, comp) for path, comp in fe_routes if comp not in imports and comp not in ('Navigate',)]
    out['frontend'] = {'route_count': len(fe_routes), 'page_files': len(pages),
                       'routes_missing_component_import': missing_page_import}

    # ---- capability registry reconciliation ----
    caps = [c async for c in db.capability_registry.find({})]
    recon = {'registered_and_implemented': [], 'registered_owner_file_missing': [],
             'registered_route_no_page': [], 'merged': [], 'deprecated': [], 'future_reserved': [],
             'inherited': []}
    fe_route_set = {'/' + p for p, _ in fe_routes} | {p for p, _ in fe_routes}
    for c in caps:
        cid, owner, route, status = c.get('id'), c.get('owner') or '', c.get('route') or '', c.get('status')
        if status == 'merged':
            recon['merged'].append(cid); continue
        if status == 'deprecated':
            recon['deprecated'].append(cid); continue
        if status == 'future':
            recon['future_reserved'].append(cid); continue
        if status == 'inherited':
            recon['inherited'].append(cid)
        # owner file existence (owner may be file or dir or "merged")
        owner_ok = True
        if owner and owner not in ('merged',):
            cand = os.path.join(BACKEND, owner.rstrip('/'))
            owner_ok = os.path.exists(cand) or os.path.exists(cand + '.py') or glob.glob(cand + '*')
        # route page existence
        route_ok = (not route) or (route in fe_route_set) or any(route.strip('/') == p.strip('/') for p, _ in fe_routes)
        if not owner_ok:
            recon['registered_owner_file_missing'].append({'id': cid, 'owner': owner})
        elif not route_ok:
            recon['registered_route_no_page'].append({'id': cid, 'route': route})
        else:
            recon['registered_and_implemented'].append(cid)
    out['capability_recon'] = {k: (v if isinstance(v, list) and (not v or isinstance(v[0], dict)) else v) for k, v in recon.items()}
    out['capability_counts'] = {k: len(v) for k, v in recon.items()}

    # ---- frontend routes NOT in capability registry (implemented but maybe not registered) ----
    cap_routes = {(c.get('route') or '').strip('/') for c in caps}
    fe_only = sorted({p.strip('/') for p, _ in fe_routes if p and p.strip('/') not in cap_routes and not p.startswith(':')})
    out['frontend_routes_not_in_registry'] = fe_only

    # ---- standards / governance registries ----
    async def cnt(c):
        return await db[c].count_documents({})
    out['standards'] = {c: await cnt(c) for c in
                        ['qiks_standards', 'constitutional_registry', 'trust_registry', 'factory_constitution',
                         'constitution_versions', 'qbos_versions', 'qeds_versions', 'qics_portals']}
    # ---- agents / digital workforce ----
    out['agents'] = {c: await cnt(c) for c in ['registry_agents', 'digital_employees', 'll_pilots', 'pilot_reports']}
    # ---- recipes / inheritance ----
    out['recipes'] = {c: await cnt(c) for c in ['inherited_products', 'inherited_products', 'kr_lineage', 'kr_enterprise_memory', 'product_families']}
    # ---- PMS / PMF (production mfg system / fit) — acceptance & order records ----
    out['pms_pmf'] = {c: await cnt(c) for c in
                      ['production_acceptance_records', 'distribution_acceptance_records', 'manufacturing_orders',
                       'manufacturing_jobs', 'production_orders', 'production_line_runs', 'manufacturing_batches']}
    # ---- founder approvals / governance decisions ----
    out['founder_approvals'] = {c: await cnt(c) for c in
                                ['founder_escalations', 'production_acceptance_records', 'distribution_acceptance_records',
                                 'after_action_reviews', 'factory_audits', 'qa_cleanup_audit']}
    # proposals on disk
    out['proposals_on_disk'] = sorted(glob.glob('/app/memory/proposals/*') + glob.glob('/app/migration_packages/*'))

    # ---- lessons / products ----
    out['products_lessons'] = {c: await cnt(c) for c in
                               ['products', 'engine_products', 'media_products', 'qiks_lessons', 'knowledge_records',
                                'knowledge_engine_records', 'book_records', 'decoder_records', 'colleges', 'topic_registry']}

    # ---- duplicate/overlap signals in capability registry (same route or same owner) ----
    from collections import defaultdict
    byroute = defaultdict(list); byowner = defaultdict(list)
    for c in caps:
        if c.get('route'): byroute[c['route']].append(c['id'])
        if c.get('owner'): byowner[c['owner']].append(c['id'])
    out['dup_route'] = {k: v for k, v in byroute.items() if len(v) > 1}
    out['dup_owner'] = {k: v for k, v in byowner.items() if len(v) > 1}

    print(json.dumps(out, indent=1, default=str))

asyncio.run(main())
