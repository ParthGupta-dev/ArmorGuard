import asyncio
from agent.governance.armoriq_client import client
from agent.tools.nmap_tool import run_nmap_scan
from armoriq_sdk import PolicyBlockedException

async def main():
    print("Testing nmap tool wrapped with ArmorIQ flow...")
    
    plan = {
        "steps": [
            {"action": "nmap"}
        ]
    }
    
    plan_capture = client.capture_plan(
        llm="gemini",
        prompt="Scan localhost using nmap",
        plan=plan
    )
    intent_token = client.get_intent_token(plan_capture)
    
    # Test A: Happy Path (localhost)
    print("\n--- Test A: Happy Path ---")
    try:
        findings = run_nmap_scan("localhost", "test-scan-id", client, intent_token)
        print(f"Happy path succeeded! Found {len(findings)} findings.")
    except Exception as e:
        print("Happy path failed:", type(e), e)
        
    # Test B: Out of Scope Target
    print("\n--- Test B: Out of Scope Target ---")
    try:
        run_nmap_scan("google.com", "test-scan-id", client, intent_token)
        print("Out of scope target allowed (ERROR)")
    except PolicyBlockedException as e:
        print("Blocked out-of-scope target (SUCCESS):", e)
        print("Reason:", e.reason)
        print("Classification:", getattr(e, "metadata", {}).get("drift_classification"))

if __name__ == "__main__":
    asyncio.run(main())
