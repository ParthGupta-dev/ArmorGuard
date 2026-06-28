from typing import List

# Order matters — the pipeline runs strictly left to right:
#   discovery (katana crawl, ffuf route brute) → parameter discovery (arjun) →
#   probe/attack (httpx, nuclei, nikto, sqlmap).
# Attack tools read the endpoints/parameters discovery wrote into the scan context,
# so discovery MUST precede them. arjun must precede sqlmap (it supplies the params).
TOOLS_BY_MODE = {
    "default": ["nmap", "katana", "ffuf", "httpx", "nuclei"],
    "deep":    ["nmap", "katana", "ffuf", "arjun", "httpx", "nuclei", "nikto", "sqlmap", "hydra"],
}
VALID_TOOLS = set(TOOLS_BY_MODE["deep"])


def get_tools_for_mode(scan_mode: str, selected_tools: List[str]) -> List[str]:
    if scan_mode == "custom":
        return [t for t in selected_tools if t in VALID_TOOLS]
    return TOOLS_BY_MODE.get(scan_mode, TOOLS_BY_MODE["default"])


def build_armoriq_plan(tools: List[str], target_url: str, scan_mode: str) -> dict:
    """Each plan step now carries the actual target and scan mode, not just a bare
    action name — ArmorIQ's policy decision needs to know *what* it's evaluating, not
    only which tool is about to run. "http_request" is also registered here even though
    it's not a scan tool: the post-scan summary agent can call it, and that call must be
    checked by the exact same governance gate as every scan tool, not skipped."""
    steps = [{"action": t, "target": target_url, "scan_mode": scan_mode} for t in tools]
    steps.append({"action": "http_request", "target": target_url, "scan_mode": scan_mode})
    return {"steps": steps}