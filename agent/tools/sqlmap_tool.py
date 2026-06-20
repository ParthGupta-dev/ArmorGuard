import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from agent.config import SQLMAP_PATH


def run_sqlmap_scan(
    target_url: str,
    scan_id: str,
    client: Optional[Any] = None,
    intent_token: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    print(f"[sqlmap_tool] Starting sqlmap scan against: {target_url}")

    if client is not None and intent_token is not None:
        print("[sqlmap_tool] Verifying intent with ArmorIQ...")
        client.invoke(
            mcp="agent_tools",
            action="sqlmap",
            intent_token=intent_token,
            params={"target": target_url},
        )
        print("[sqlmap_tool] Intent verified successfully by ArmorIQ.")

    # Probe a parameterised endpoint — demo target exposes /search?q=
    probe_url = urljoin(target_url.rstrip("/") + "/", "search?q=test")

    tmpdir = tempfile.mkdtemp(prefix="sqlmap_")
    try:
        cmd = [
            sys.executable, SQLMAP_PATH,
            "-u", probe_url,
            "--batch",
            "--level=1",
            "--risk=1",
            "--forms",
            "--output-dir", tmpdir,
            "--timeout=20",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        output = (result.stdout + result.stderr).lower()

        findings: List[Dict[str, Any]] = []

        if "is vulnerable" in output or "injection point" in output:
            findings.append({
                "findingId": str(uuid.uuid4()),
                "scanId": scan_id,
                "severity": "Critical",
                "title": "SQL Injection Vulnerability Confirmed",
                "description": (
                    f"sqlmap confirmed a SQL injection vulnerability at {probe_url}. "
                    "An attacker can manipulate database queries to extract, modify, or delete data."
                ),
                "remediation": (
                    "Use parameterised queries or prepared statements for all database interactions. "
                    "Never concatenate user input directly into SQL strings. "
                    "Apply an input validation and WAF layer as defence-in-depth."
                ),
                "evidence": f"sqlmap target: {probe_url}\nVerdict: SQL injection confirmed.\n{result.stdout[:500]}",
                "createdAt": datetime.utcnow().isoformat() + "Z",
            })
        elif "might be injectable" in output or "parameter appears to be" in output:
            findings.append({
                "findingId": str(uuid.uuid4()),
                "scanId": scan_id,
                "severity": "High",
                "title": "Potential SQL Injection Parameter Detected",
                "description": (
                    f"sqlmap identified a parameter at {probe_url} that may be injectable. "
                    "Further manual testing is recommended to confirm exploitability."
                ),
                "remediation": (
                    "Review all user-supplied inputs used in database queries. "
                    "Switch to parameterised queries or an ORM to eliminate injection risk."
                ),
                "evidence": f"sqlmap target: {probe_url}\nVerdict: Parameter flagged as potentially injectable.\n{result.stdout[:500]}",
                "createdAt": datetime.utcnow().isoformat() + "Z",
            })

        print(f"[sqlmap_tool] Completed scan. Found {len(findings)} finding(s).")
        return findings

    except subprocess.TimeoutExpired:
        print("[sqlmap_tool] WARNING: sqlmap subprocess timed out.")
        return []
    except Exception as e:
        print(f"[sqlmap_tool] WARNING: Error running sqlmap — {e}")
        return []
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
