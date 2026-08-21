"""QRU Factory package intake: validate, dedupe, durably stage, never publish."""
from __future__ import annotations
import hashlib, io, json, logging, mimetypes, posixpath, re, stat, uuid, zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping, Optional

log = logging.getLogger("qru.package_intake")
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 250 * 1024 * 1024
MAX_MEMBER_BYTES = 100 * 1024 * 1024
MAX_MEMBERS = 100
MAX_JSON_BYTES = 2 * 1024 * 1024

class PackageIntakeError(Exception):
    def __init__(self, code, stage, message, *, trace_id=None, http_status=400, details=None):
        super().__init__(message); self.code=code; self.stage=stage; self.message=message
        self.trace_id=trace_id; self.http_status=http_status; self.details=details or {}
    def as_dict(self):
        out={"ok":False,"code":self.code,"stage":self.stage,"trace_id":self.trace_id,"message":self.message}
        if self.details: out["details"]=self.details
        return out

@dataclass(frozen=True)
class ParsedFactoryPackage:
    trace_id: str; archive_sha256: str; product_key: str; version: str
    manifest_name: str; manifest: Mapping[str,Any]; metadata_name: str
    metadata: Mapping[str,Any]; approval: Mapping[str,Any]; members: Mapping[str,bytes]
    declared_files: list[Mapping[str,str]]
    @property
    def idempotency_key(self): return f"{self.product_key}:{self.version}:{self.archive_sha256}"
    @property
    def version_key(self): return f"{self.product_key}:{self.version}"

def new_trace_id(): return f"qru-ingest-{uuid.uuid4().hex}"
def _fail(code,stage,msg,trace,status=400,details=None):
    raise PackageIntakeError(code,stage,msg,trace_id=trace,http_status=status,details=details)
def _norm(v): return re.sub(r"\s+"," ",str(v or "").strip().upper().replace("_"," "))
def _safe(name,trace):
    if not name or "\\" in name or "\x00" in name: _fail("UNSAFE_ARCHIVE_PATH","archive_safety","Archive contains an invalid member path.",trace,details={"member":name})
    p=PurePosixPath(name); norm=posixpath.normpath(name)
    if p.is_absolute() or any(x in ("",".","..") for x in p.parts) or norm!=name or norm.startswith("../"):
        _fail("UNSAFE_ARCHIVE_PATH","archive_safety","Archive contains an unsafe member path.",trace,details={"member":name})
    return name
def _j(name,data,trace):
    if len(data)>MAX_JSON_BYTES: _fail("JSON_TOO_LARGE","contract_discovery",f"{name} is too large.",trace)
    try: value=json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError,json.JSONDecodeError): _fail("INVALID_JSON","contract_discovery",f"{name} is not valid UTF-8 JSON.",trace)
    if not isinstance(value,dict): _fail("INVALID_JSON_SHAPE","contract_discovery",f"{name} must be a JSON object.",trace)
    return value
def _manifest(d):
    f=d.get("files")
    return bool(d.get("product_key") and d.get("version") and isinstance(f,list) and f and all(isinstance(x,dict) and isinstance(x.get("filename"),str) and isinstance(x.get("sha256"),str) for x in f))
def _approved(d):
    for k in ("founder_approval","approval_status","status","founder_status"):
        v=_norm(d.get(k))
        if not v or any(x in v for x in ("PENDING","REJECT","DENIED","NOT APPROVED","DECLINED")): continue
        if v in ("TRUE","YES","APPROVED","FOUNDER APPROVED","APPROVED BY FOUNDER","AUTHORIZED") or ("APPROVED" in v and "FOUNDER" in v): return True
    return False
def _locked(*docs):
    for d in docs:
        v=_norm(d.get("publisher_handoff"))
        if "LOCKED" in v: return d.get("publisher_handoff")
    return None
def _fmt(name): return name.rsplit(".",1)[-1].lower() if "." in name else "bin"
def _mime(name): return mimetypes.guess_type(name)[0] or "application/octet-stream"
def _fid_part(v,n=60): return (re.sub(r"[^a-zA-Z0-9._-]+","-",v).strip("-.") or "product")[:n]

def parse_factory_package(blob: bytes, *, trace_id: Optional[str]=None) -> ParsedFactoryPackage:
    trace=trace_id or new_trace_id()
    if not isinstance(blob,(bytes,bytearray)): _fail("INVALID_PACKAGE_BODY","receive","Package body must be ZIP bytes.",trace)
    blob=bytes(blob)
    if not blob: _fail("EMPTY_PACKAGE","receive","Package is empty.",trace)
    if len(blob)>MAX_ARCHIVE_BYTES: _fail("PACKAGE_TOO_LARGE","receive","Package exceeds the 100 MB intake limit.",trace,413)
    archive_sha=hashlib.sha256(blob).hexdigest()
    try: z=zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile: _fail("INVALID_ZIP","archive_open","Package is not a valid ZIP archive.",trace)
    members={}; seen=set(); total=0
    with z:
        infos=[i for i in z.infolist() if not i.is_dir()]
        if not infos: _fail("EMPTY_ZIP","archive_safety","ZIP contains no files.",trace)
        if len(infos)>MAX_MEMBERS: _fail("TOO_MANY_FILES","archive_safety",f"ZIP contains more than {MAX_MEMBERS} files.",trace)
        for i in infos:
            name=_safe(i.filename,trace)
            if name in seen: _fail("DUPLICATE_ARCHIVE_MEMBER","archive_safety","ZIP contains duplicate filenames.",trace,details={"member":name})
            seen.add(name); mode=(i.external_attr>>16)&0xFFFF
            if mode and stat.S_ISLNK(mode): _fail("UNSAFE_ARCHIVE_SYMLINK","archive_safety","ZIP symlinks are not accepted.",trace,details={"member":name})
            if i.file_size>MAX_MEMBER_BYTES: _fail("MEMBER_TOO_LARGE","archive_safety",f"{name} exceeds the per-file limit.",trace)
            total+=i.file_size
            if total>MAX_UNCOMPRESSED_BYTES: _fail("UNCOMPRESSED_PACKAGE_TOO_LARGE","archive_safety","Expanded package exceeds the intake limit.",trace)
            try: members[name]=z.read(i)
            except (RuntimeError,zipfile.BadZipFile) as e: _fail("ZIP_READ_FAILED","archive_read",f"Could not read {name}: {e}",trace)
    docs={n:_j(n,b,trace) for n,b in members.items() if n.lower().endswith(".json")}
    mans=[(n,d) for n,d in docs.items() if _manifest(d)]
    if len(mans)!=1: _fail("MANIFEST_NOT_UNIQUE","contract_discovery","Factory package must contain exactly one manifest JSON.",trace,details={"candidates":[n for n,_ in mans]})
    mn,m=mans[0]; key=str(m["product_key"]).strip(); ver=str(m["version"]).strip(); declared=[]; names=set()
    for e in m["files"]:
        name=_safe(str(e["filename"]),trace); sha=str(e["sha256"]).strip().lower()
        if name in names: _fail("DUPLICATE_MANIFEST_FILE","manifest_validation","Manifest lists a file more than once.",trace,details={"filename":name})
        if not re.fullmatch(r"[0-9a-f]{64}",sha): _fail("INVALID_MANIFEST_SHA256","manifest_validation","Manifest contains an invalid SHA-256.",trace,details={"filename":name})
        if name not in members: _fail("MANIFEST_FILE_MISSING","manifest_validation","Manifest references a missing file.",trace,details={"filename":name})
        actual=hashlib.sha256(members[name]).hexdigest()
        if actual!=sha: _fail("CHECKSUM_MISMATCH","checksum_validation","Artifact checksum does not match manifest.",trace,details={"filename":name,"expected":sha,"actual":actual})
        names.add(name); declared.append({"filename":name,"sha256":sha})
    extras=set(members)-names-{mn}
    if extras: _fail("UNDECLARED_ARCHIVE_FILE","manifest_validation","ZIP contains files not declared by the manifest.",trace,details={"files":sorted(extras)})
    an=next((n for n in names if PurePosixPath(n).name.lower()=="approval-record.json"),None)
    if not an: _fail("APPROVAL_RECORD_MISSING","approval_gate","Factory package has no approval-record.json.",trace)
    approval=docs.get(an) or _j(an,members[an],trace)
    metas=[(n,docs[n]) for n in names if n.lower().endswith(".json") and n!=an and n in docs and str(docs[n].get("product_key","")).strip()==key and str(docs[n].get("version","")).strip()==ver and any(k in docs[n] for k in ("title","category","tags"))]
    if len(metas)!=1: _fail("METADATA_NOT_UNIQUE","contract_discovery","Factory package must contain exactly one product metadata JSON.",trace,details={"candidates":[n for n,_ in metas]})
    metan,meta=metas[0]
    for label,d in (("metadata",meta),("approval",approval)):
        if str(d.get("product_key","")).strip()!=key or str(d.get("version","")).strip()!=ver: _fail("IDENTITY_MISMATCH","identity",f"{label} identity does not match the manifest.",trace)
    if not _approved(approval): _fail("FOUNDER_APPROVAL_REQUIRED","approval_gate","Package is valid but Founder approval is not granted.",trace,409)
    lock=_locked(approval,m)
    if lock: _fail("PUBLISHER_HANDOFF_LOCKED","approval_gate","Package still declares publisher handoff as locked.",trace,409,{"publisher_handoff":lock})
    return ParsedFactoryPackage(trace,archive_sha,key,ver,mn,m,metan,meta,approval,members,declared)

async def _stage(db,intake,trace,stage,status,msg=""):
    from models import now_iso
    event={"stage":stage,"status":status,"at":now_iso()}
    if msg: event["message"]=msg[:500]
    await db.package_intakes.update_one({"_id":intake},{"$set":{"stage":stage,"updated_at":now_iso()},"$push":{"stage_events":event}})
    log.info("[%s] %s %s",trace,stage,status)

async def ingest_factory_package(blob: bytes, *, actor="Founder", trace_id=None) -> dict:
    """Stage an approved Factory ZIP as Ready for Publisher. Never publishes it."""
    from pymongo import ReturnDocument
    from pymongo.errors import DuplicateKeyError
    from database import db
    import storage
    from models import now_iso
    trace=trace_id or new_trace_id(); p=parse_factory_package(blob,trace_id=trace); intake=p.idempotency_key
    claim={"_id":p.version_key,"product_key":p.product_key,"version":p.version,"archive_sha256":p.archive_sha256,"intake_id":intake,"created_at":now_iso()}
    try: vc=await db.package_version_claims.find_one_and_update({"_id":p.version_key},{"$setOnInsert":claim},upsert=True,return_document=ReturnDocument.AFTER)
    except DuplicateKeyError: vc=await db.package_version_claims.find_one({"_id":p.version_key})
    if not vc or vc.get("archive_sha256")!=p.archive_sha256:
        raise PackageIntakeError("PRODUCT_VERSION_CONFLICT","idempotency","This product_key/version is already claimed by different package bytes.",trace_id=trace,http_status=409,details={"existing_sha256":(vc or {}).get("archive_sha256"),"incoming_sha256":p.archive_sha256})
    old=await db.package_intakes.find_one({"_id":intake},{"_id":0})
    if old and old.get("status")=="complete":
        return {"ok":True,"idempotent_replay":True,"trace_id":trace,"original_trace_id":old.get("trace_id"),"product_id":old.get("product_id"),"product_key":p.product_key,"version":p.version,"archive_sha256":p.archive_sha256,"status":"Ready for Publisher","published":False}
    if old and old.get("status")=="processing":
        prod=await db.products.find_one({"_id":f"package:{intake}"},{"_id":0,"id":1})
        if prod:
            pid=prod.get("id") or f"pkg-{p.archive_sha256[:24]}"
            await db.package_intakes.update_one({"_id":intake},{"$set":{"status":"complete","stage":"complete","product_id":pid,"updated_at":now_iso(),"published":False,"recovered_after_restart":True},"$push":{"stage_events":{"stage":"complete","status":"recovered","at":now_iso()}}})
            return {"ok":True,"idempotent_replay":True,"recovered_after_restart":True,"trace_id":trace,"original_trace_id":old.get("trace_id"),"product_id":pid,"product_key":p.product_key,"version":p.version,"archive_sha256":p.archive_sha256,"status":"Ready for Publisher","published":False}
        raise PackageIntakeError("INGEST_IN_PROGRESS","idempotency","This exact package is already being ingested.",trace_id=trace,http_status=409,details={"original_trace_id":old.get("trace_id")})
    doc={"_id":intake,"idempotency_key":intake,"trace_id":trace,"product_key":p.product_key,"version":p.version,"archive_sha256":p.archive_sha256,"status":"processing","stage":"validated","actor":actor,"manifest_name":p.manifest_name,"created_at":old.get("created_at") if old else now_iso(),"updated_at":now_iso(),"stage_events":[{"stage":"validated","status":"ok","at":now_iso()}]}
    await db.package_intakes.replace_one({"_id":intake},doc,upsert=True)
    try:
        await _stage(db,intake,trace,"durable_storage","started")
        key=_fid_part(p.product_key); ver=_fid_part(p.version,24); arts=[]; customer=[]
        for e in p.declared_files:
            src=e["filename"]; ext=_fmt(src); fid=f"deliverable-{key}-{ver}-{e['sha256'][:12]}.{ext}"; data=p.members[src]
            if not await storage.amirror_file(fid,data,_mime(src)): raise PackageIntakeError("DURABLE_STORAGE_FAILED","durable_storage",f"Durable storage could not verify {src}.",trace_id=trace,http_status=503,details={"filename":src})
            art={"source_filename":src,"filename":fid,"format":ext,"media_type":_mime(src),"sha256":e["sha256"],"size":len(data),"storage_path":storage.asset_object_path(fid)}; arts.append(art)
            if ext=="pdf": customer.append({k:art[k] for k in ("filename","format","media_type","sha256","size")})
        msha=hashlib.sha256(p.members[p.manifest_name]).hexdigest(); mfid=f"deliverable-{key}-{ver}-{msha[:12]}.manifest.json"; zfid=f"deliverable-{key}-{ver}-{p.archive_sha256[:12]}.package.zip"
        if not await storage.amirror_file(mfid,p.members[p.manifest_name],"application/json"): raise PackageIntakeError("DURABLE_STORAGE_FAILED","durable_storage","Durable storage could not verify the package manifest.",trace_id=trace,http_status=503)
        if not await storage.amirror_file(zfid,blob,"application/zip"): raise PackageIntakeError("DURABLE_STORAGE_FAILED","durable_storage","Durable storage could not verify the original package ZIP.",trace_id=trace,http_status=503)
        await _stage(db,intake,trace,"durable_storage","ok"); await _stage(db,intake,trace,"catalog_stage","started")
        pid=f"pkg-{p.archive_sha256[:24]}"; product={"_id":f"package:{intake}","id":pid,"product_code":f"PKG-{p.archive_sha256[:12].upper()}","product_key":p.product_key,"version":p.version,"title":str(p.metadata.get("title") or p.product_key),"subtitle":p.metadata.get("subtitle"),"product_type":p.metadata.get("product_type") or "Publisher Package","family":p.metadata.get("series") or p.metadata.get("category") or "General","category":p.metadata.get("category"),"tags":p.metadata.get("tags") or [],"price":p.metadata.get("suggested_price_usd"),"status":"Ready for Publisher","production_state":"Gold Master","source":"factory_package_intake","deliverable_ready":bool(customer),"customer_deliverable":{"files":customer,"source":"factory_package_intake"},"package_artifacts":arts,"package_manifest":{"filename":mfid,"source_filename":p.manifest_name,"sha256":msha,"storage_path":storage.asset_object_path(mfid)},"source_package":{"filename":zfid,"sha256":p.archive_sha256,"storage_path":storage.asset_object_path(zfid)},"factory_approval":dict(p.approval),"package_intake_key":intake,"package_trace_id":trace,"published":False,"created_by":actor,"created_at":now_iso(),"updated_at":now_iso()}
        try: await db.products.insert_one(product)
        except DuplicateKeyError:
            if not await db.products.find_one({"_id":product["_id"]}): raise
        await _stage(db,intake,trace,"catalog_stage","ok")
        await db.package_intakes.update_one({"_id":intake},{"$set":{"status":"complete","stage":"complete","product_id":pid,"updated_at":now_iso(),"published":False},"$push":{"stage_events":{"stage":"complete","status":"ok","at":now_iso()}}})
        return {"ok":True,"idempotent_replay":False,"trace_id":trace,"product_id":pid,"product_key":p.product_key,"version":p.version,"archive_sha256":p.archive_sha256,"status":"Ready for Publisher","artifact_count":len(arts),"customer_file_count":len(customer),"published":False}
    except PackageIntakeError as e:
        await db.package_intakes.update_one({"_id":intake},{"$set":{"status":"failed","stage":e.stage,"error_code":e.code,"error_message":e.message[:500],"updated_at":now_iso()},"$push":{"stage_events":{"stage":e.stage,"status":"failed","code":e.code,"message":e.message[:500],"at":now_iso()}}}); raise
    except Exception as e:
        await db.package_intakes.update_one({"_id":intake},{"$set":{"status":"failed","stage":"internal","error_code":"INGEST_INTERNAL_ERROR","error_message":str(e)[:500],"updated_at":now_iso()}})
        raise PackageIntakeError("INGEST_INTERNAL_ERROR","internal","Package intake failed unexpectedly.",trace_id=trace,http_status=500) from e
