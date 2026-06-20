import subprocess
from urllib.parse import urlparse
from typing import List

def run_hydra_scan(target_url: str, scan_id: str) -> List[dict]:
    findings = []
    
    # 1. Cleanly parse the URL to satisfy Hydra's strict argument format
    parsed_url = urlparse(target_url)
    host = parsed_url.hostname
    port = str(parsed_url.port) if parsed_url.port else "80"
    path = parsed_url.path if parsed_url.path else "/"
    
    if not host:
        return [{"tool": "hydra", "severity": "error", "title": "Malformed URL", "description": f"Could not parse host from {target_url}"}]

    # 2. Build the command using proper structural arguments
    cmd = [
        "hydra",
        "-l", "admin",
        "-p", "admin", # Ideally replace with -P path_to_wordlist for real agent utility
        "-s", port,
        host,
        "http-get",
        path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Default security footprint
        severity = "info"
        title = "Hydra Authentication Check completed"
        description = "No weak credentials detected."

        # 3. Dynamic string parsing so the agent actually understands a success
        if "login:" in result.stdout.lower() or "valid" in result.stdout.lower():
            severity = "critical"
            title = "Critical Vulnerability: Weak Authentication Found"
            description = f"Hydra successfully cracked the service:\n{result.stdout}"
            
        findings.append({
            "tool": "hydra",
            "severity": severity,
            "title": title,
            "description": description[:2000]
        })

    except Exception as e:
        findings.append({
            "tool": "hydra",
            "severity": "low",
            "title": "Hydra Execution Error",
            "description": str(e)
        })

    return findings
