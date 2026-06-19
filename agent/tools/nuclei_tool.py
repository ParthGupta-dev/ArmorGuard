import json
import subprocess
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent.config import NUCLEI_PATH

_SEVERITY_MAP = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "info": "Low",
}


def run_nuclei_scan(
    target_url: str,
    scan_id: str,
    client: Optional[Any] = None,
    intent_token: Optional[Any] = None,
    aggressive: bool = False,
) -> List[Dict[str, Any]]:
    print(f"[nuclei_tool] Starting Nuclei scan against: {target_url} (aggressive={aggressive})")

    if client is not None and intent_token is not None:
        print("[nuclei_tool] Verifying intent with ArmorIQ...")
        client.invoke(
            mcp="agent_tools",
            action="nuclei",
            intent_token=intent_token,
            params={"target": target_url},
        )
        print("[nuclei_tool] Intent verified successfully by ArmorIQ.")

    tags = "misconfig,default-login,exposure,headers"
    if aggressive:
        tags += ",cve"

    cmd = [NUCLEI_PATH, "-u", target_url, "-json", "-silent", "-tags", tags]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout.strip()

        if not output:
            print("[nuclei_tool] No findings from Nuclei.")
            return []

        findings = []
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            info = obj.get("info", {})
            raw_severity = info.get("severity", "info").lower()
            severity = _SEVERITY_MAP.get(raw_severity, "Low")

            name = info.get("name", obj.get("template-id", "Unknown Finding"))
            description = info.get("description", f"Nuclei detected: {name}")
            remediation = info.get("remediation") or "Review the flagged configuration and apply security hardening."
            matched_at = obj.get("matched-at", target_url)
            extracted = obj.get("extracted-results") or []
            evidence = f"Template: {obj.get('template-id', 'unknown')}\nMatched at: {matched_at}"
            if extracted:
                evidence += f"\nExtracted: {'; '.join(str(x) for x in extracted[:3])}"

            findings.append({
                "findingId": str(uuid.uuid4()),
                "scanId": scan_id,
                "severity": severity,
                "title": name,
                "description": description,
                "remediation": remediation,
                "evidence": evidence,
                "createdAt": datetime.utcnow().isoformat() + "Z",
            })

        print(f"[nuclei_tool] Completed scan. Found {len(findings)} finding(s).")
        return findings

    except subprocess.TimeoutExpired:
        print("[nuclei_tool] WARNING: Nuclei subprocess timed out.")
        return []
    except Exception as e:
        print(f"[nuclei_tool] WARNING: Error running nuclei — {e}")
        return []
