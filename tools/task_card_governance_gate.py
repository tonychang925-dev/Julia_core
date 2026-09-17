#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, os, re, subprocess, sys, urllib.error, urllib.request
from pathlib import Path
from typing import Iterable

MANDATORY_TASK_FIELDS=("FROZEN_AUTHORITY_TRACE","RULE11_CLASSIFICATION","CURRENT_PHASE","TARGET_REQUIREMENT","DEFERRED_FINDINGS","TASK_ID","REPO","TARGET_BRANCH","BASE_SHA","AUTHORIZED_PATHS","FORBIDDEN_PATHS","REQUIRED_BEHAVIOR","FORBIDDEN_BEHAVIOR","ACCEPTANCE_EVIDENCE")
MANDATORY_SELF_CHECK_FIELDS=("AUTHOR_ROLE","TASK_ID","TASK_CARD_VERSION","AUTHORITY_SOURCE_FILES_CHECKED","CURRENT_MAIN_SHAS","MANDATORY_TASK_FIELDS_PRESENT","AUTHORIZED_PATH_COUNT","DEFERRED_FINDING_COUNT","AUTHORITY_IDENTITY","MANDATORY_HEADER","RULE11_CLASSIFICATION_CHECK","PHASE_SCOPE_CHECK","RESIDUAL_DECISION_AUDIT","RESIDUAL_ARCHITECTURE_DECISIONS","RESIDUAL_CONTRACT_SEMANTIC_DECISIONS","CROSS_BOUNDARY_SEMANTICS","CURRENT_CODE_COMPATIBILITY","ACCEPTANCE_EVIDENCE_CHECK","NO_AGENT_ARCHITECTURE_DISCRETION","SELF_CHECK_RESULT","READY_FOR_SUBMISSION")
MANDATORY_PERMISSION_FIELDS=("PERMISSION_MODEL","PERMISSION_REPOSITORY","PERMISSION_BASE_SHA","PERMISSION_TARGET_BRANCH","READ_SCOPE","WRITE_SCOPE","ARCHITECTURE_MUTATION","PUBLIC_CONTRACT_MUTATION","CROSS_BOUNDARY_SEMANTIC_DECISION","DEPENDENCY_MUTATION","TEST_CREATION","BRANCH_CREATION","COMMIT","PR_CREATION","MERGE","RELEASE","DEPLOY","PRODUCTION_MUTATION","FALLBACK","SYNTHETIC_SUCCESS","FUTURE_PHASE_SCOPE")
MANDATORY_DENY=("ARCHITECTURE_MUTATION","CROSS_BOUNDARY_SEMANTIC_DECISION","MERGE","RELEASE","DEPLOY","PRODUCTION_MUTATION","FALLBACK","SYNTHETIC_SUCCESS","FUTURE_PHASE_SCOPE")
CROSS_BOUNDARY_TOKENS=("adapter","bridge","translator","proxy","serializer","provider wrapper","public boundary conversion","cross-repo contract conversion")
CROSS_BOUNDARY_REQUIRED=("SOURCE_CONTRACT","TARGET_CONTRACT","FIELD_MAPPING","STATUS_MAPPING","FAILURE_MAPPING","PROVENANCE_MAPPING","AUTHORITY_TRANSFER","MALFORMED_INPUT_BEHAVIOR","UNKNOWN_VALUE_BEHAVIOR","LIFECYCLE_OWNERSHIP")
CONTROL_PLANE_EXCLUSIONS={"docs/governance/RD1_AGENT_TASK_AUTHORITY_HEADER_TEMPLATE.md","docs/governance/RD1_TASK_CARD_AUTHOR_PRE_SUBMISSION_SELF_CHECK.md","docs/governance/RD1_ARCHITECTURE_AUTHORITY_PRECHECK.md","docs/governance/RD1_TASK_CARD_CI_PARSER_GATE.md","docs/governance/RD1_AGENT_EXECUTION_PERMISSION_MATRIX.md"}
SHA_RE=re.compile(r"^[0-9a-f]{40}$")

def _field_value(text,key):
    m=re.search(rf"(?m)^\s*{re.escape(key)}\s*\n\s*=\s*([^\n]+)",text)
    if m:return m.group(1).strip()
    m=re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*([^\n]+)",text)
    return m.group(1).strip() if m else None

def _has_field(text,key): return _field_value(text,key) is not None or re.search(rf"(?m)^\s*{re.escape(key)}\s*$",text) is not None

def _int_value(text,key):
    v=_field_value(text,key)
    if v is None:return None
    m=re.search(r"-?\d+",v); return int(m.group(0)) if m else None

def looks_like_task_card(path,text):
    normalized=path.replace("\\","/")
    if normalized in CONTROL_PLANE_EXCLUSIONS:return False
    if normalized!="PR_BODY" and Path(normalized).suffix.lower() not in {".md",".markdown"}:return False
    name=Path(path).name.lower()
    return "task_card" in name or "task-card" in name or "task card" in name or "TASK_CARD_AUTHOR_SELF_CHECK" in text or (_has_field(text,"TASK_ID") and _has_field(text,"BASE_SHA") and _has_field(text,"REPO"))

def is_cross_boundary_task(text): return any(t in text.lower() for t in CROSS_BOUNDARY_TOKENS)

def validate_task_card(text,*,path="<memory>"):
    errors=[]
    missing=[k for k in MANDATORY_TASK_FIELDS if not _has_field(text,k)]
    if missing:errors.append("missing mandatory task fields: "+", ".join(missing))
    if "TASK_CARD_AUTHOR_SELF_CHECK" not in text:errors.append("missing TASK_CARD_AUTHOR_SELF_CHECK block")
    missing=[k for k in MANDATORY_SELF_CHECK_FIELDS if not _has_field(text,k)]
    if missing:errors.append("missing self-check fields: "+", ".join(missing))
    if "AGENT_EXECUTION_PERMISSION_MATRIX" not in text:errors.append("missing AGENT_EXECUTION_PERMISSION_MATRIX block")
    missing=[k for k in MANDATORY_PERMISSION_FIELDS if not _has_field(text,k)]
    if missing:errors.append("missing permission-matrix fields: "+", ".join(missing))

    expected={"AUTHORITY_IDENTITY":"PASS","MANDATORY_HEADER":"PASS","RULE11_CLASSIFICATION_CHECK":"PASS","PHASE_SCOPE_CHECK":"PASS","RESIDUAL_DECISION_AUDIT":"PASS","CURRENT_CODE_COMPATIBILITY":"PASS","ACCEPTANCE_EVIDENCE_CHECK":"PASS","NO_AGENT_ARCHITECTURE_DISCRETION":"PASS","SELF_CHECK_RESULT":"PASS","READY_FOR_SUBMISSION":"YES","PERMISSION_MODEL":"DEFAULT_DENY","TEST_CREATION":"BOUNDED_TO_ACCEPTANCE_EVIDENCE","BRANCH_CREATION":"EXACT_TARGET_ONLY","COMMIT":"TASK_BRANCH_ONLY"}
    for k,e in expected.items():
        v=_field_value(text,k)
        if v is not None and v.upper()!=e:errors.append(f"{k} must be {e}, got {v!r}")
    for k in MANDATORY_DENY:
        v=_field_value(text,k)
        if v is not None and v.upper()!="DENY":errors.append(f"{k} must be DENY, got {v!r}")
    pc=_field_value(text,"PUBLIC_CONTRACT_MUTATION")
    if pc is not None and not (pc.upper()=="DENY" or pc.startswith("EXPLICITLY_AUTHORIZED:")):errors.append("PUBLIC_CONTRACT_MUTATION must be DENY or EXPLICITLY_AUTHORIZED:<scope>")
    dm=_field_value(text,"DEPENDENCY_MUTATION")
    if dm is not None and not (dm.upper()=="DENY" or dm.startswith("EXPLICITLY_AUTHORIZED:")):errors.append("DEPENDENCY_MUTATION must be DENY or EXPLICITLY_AUTHORIZED:<scope>")
    pr=_field_value(text,"PR_CREATION")
    if pr is not None and pr.upper() not in {"ALLOW","DENY"}:errors.append("PR_CREATION must be ALLOW or DENY")
    for a,b in (("PERMISSION_REPOSITORY","REPO"),("PERMISSION_BASE_SHA","BASE_SHA"),("PERMISSION_TARGET_BRANCH","TARGET_BRANCH")):
        av,bv=_field_value(text,a),_field_value(text,b)
        if av is not None and bv is not None and av!=bv:errors.append(f"{a} must exactly equal {b}")

    for k in ("RESIDUAL_ARCHITECTURE_DECISIONS","RESIDUAL_CONTRACT_SEMANTIC_DECISIONS"):
        v=_int_value(text,k)
        if v is not None and v!=0:errors.append(f"{k} must be 0, got {v}")
    c=_field_value(text,"RULE11_CLASSIFICATION")
    if c is not None and c not in {"A","B","C","D","NO_ACTIVE_FINDING"}:errors.append(f"RULE11_CLASSIFICATION has illegal value {c!r}")
    base=_field_value(text,"BASE_SHA")
    if base is not None and not SHA_RE.fullmatch(base):errors.append(f"BASE_SHA must be an exact 40-hex SHA, got {base!r}")
    if is_cross_boundary_task(text):
        miss=[k for k in CROSS_BOUNDARY_REQUIRED if not _has_field(text,k)]
        if miss:errors.append("cross-boundary task missing frozen mappings: "+", ".join(miss))
        v=_field_value(text,"CROSS_BOUNDARY_SEMANTICS")
        if v is not None and v.upper()!="PASS":errors.append(f"CROSS_BOUNDARY_SEMANTICS must be PASS, got {v!r}")
    mc=_field_value(text,"MANDATORY_TASK_FIELDS_PRESENT")
    if mc is not None:
        exp=len(MANDATORY_TASK_FIELDS); m=re.match(r"\s*(\d+)\s*/\s*(\d+)\s*$",mc)
        if not m or int(m.group(1))!=exp or int(m.group(2))!=exp:errors.append(f"MANDATORY_TASK_FIELDS_PRESENT must be {exp}/{exp}, got {mc!r}")
    return [f"{path}: {e}" for e in errors]

def github_main_sha(repo,token):
    req=urllib.request.Request(f"https://api.github.com/repos/{repo}/branches/main",headers={"Accept":"application/vnd.github+json","User-Agent":"rd1-task-card-governance-gate",**({"Authorization":f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:p=json.load(r)
    except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError) as e:raise RuntimeError(f"cannot verify current main for {repo}: {e}") from e
    sha=p.get("commit",{}).get("sha","")
    if not SHA_RE.fullmatch(sha):raise RuntimeError(f"invalid current main SHA returned for {repo}: {sha!r}")
    return sha

def validate_remote_base(text,*,token):
    repo,base=_field_value(text,"REPO"),_field_value(text,"BASE_SHA")
    if not repo or not base or not SHA_RE.fullmatch(base):return []
    cur=github_main_sha(repo,token)
    return [] if cur==base else [f"BASE_DRIFT: {repo}/main={cur}, task BASE_SHA={base}"]

def changed_files(base_ref):
    p=subprocess.run(["git","diff","--name-only",f"{base_ref}...HEAD"],check=True,text=True,capture_output=True)
    return [x.strip() for x in p.stdout.splitlines() if x.strip()]

def validate_pr_body(event_path):
    if not event_path:return []
    p=Path(event_path)
    if not p.exists():return []
    body=((json.loads(p.read_text(encoding="utf-8")).get("pull_request") or {}).get("body") or "")
    return validate_task_card(body,path="PR_BODY") if body and looks_like_task_card("PR_BODY",body) else []

def validate_paths(paths:Iterable[str],*,verify_remote,token):
    checked=[];errors=[]
    for raw in paths:
        p=Path(raw)
        if not p.exists() or p.is_dir():continue
        try:text=p.read_text(encoding="utf-8")
        except UnicodeDecodeError:continue
        if not looks_like_task_card(raw,text):continue
        checked.append(raw);errors.extend(validate_task_card(text,path=raw))
        if verify_remote:
            try:errors.extend(f"{raw}: {e}" for e in validate_remote_base(text,token=token))
            except RuntimeError as e:errors.append(f"{raw}: REMOTE_BASE_VERIFICATION_FAIL: {e}")
    return {"checked_task_cards":checked,"errors":errors}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("paths",nargs="*");ap.add_argument("--base-ref");ap.add_argument("--event-path",default=os.getenv("GITHUB_EVENT_PATH"));ap.add_argument("--verify-remote-base",action="store_true");ap.add_argument("--json",action="store_true");a=ap.parse_args()
    paths=list(a.paths)
    if a.base_ref:paths.extend(changed_files(a.base_ref))
    r=validate_paths(dict.fromkeys(paths),verify_remote=a.verify_remote_base,token=os.getenv("GITHUB_TOKEN"));r["errors"].extend(validate_pr_body(a.event_path));r["status"]="PASS" if not r["errors"] else "FAIL"
    print(json.dumps(r,indent=2,ensure_ascii=False) if a.json else f"RD1_TASK_CARD_GOVERNANCE_GATE={r['status']}\n"+"\n".join([*(f"checked: {x}" for x in r['checked_task_cards']),*(f"ERROR: {e}" for e in r['errors'])]))
    return 0 if r["status"]=="PASS" else 1

if __name__=="__main__":sys.exit(main())
