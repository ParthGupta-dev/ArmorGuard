from typing import List

TOOLS_BY_MODE = {
    "default": ["nmap", "nuclei", "httpx"],
    "deep":    ["nmap", "nuclei", "httpx", "sqlmap"],
}
VALID_TOOLS = set(TOOLS_BY_MODE["deep"])


def get_tools_for_mode(scan_mode: str, selected_tools: List[str]) -> List[str]:
    if scan_mode == "custom":
        return [t for t in selected_tools if t in VALID_TOOLS]
    return TOOLS_BY_MODE.get(scan_mode, TOOLS_BY_MODE["default"])


def build_armoriq_plan(tools: List[str], target_url: str, scan_mode: str) -> dict:
    return {"steps": [{"action": t} for t in tools]}
