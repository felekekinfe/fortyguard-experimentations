"""
Module 4: Autonomous Agentic Tool Chaining Pipeline
-----------------------------------------------------
Simulates an autonomous agent workflow that chains asynchronous MCP tools
(heatmap submission -> dynamic polling via heatmap_read) over JSON-RPC.
"""

import os
import json
import time
import requests

API_KEY = os.getenv("FORTYGUARD_API_KEY", "PASTE_YOUR_API_KEY_HERE")
MCP_ENDPOINT = "https://tos-mcp.app.fortyguard.com/mcp"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Authorization": f"Bearer {API_KEY}"
}

def mcp_call_tool(tool_name: str, arguments: dict, request_id: int = 1):
    """Invokes a specific MCP tool using standard JSON-RPC tools/call method."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": request_id
    }

    print(f"🤖 [Agent Action] Calling MCP Tool: '{tool_name}'")
    print(f"   Arguments: {json.dumps(arguments, indent=2)}")

    response = requests.post(MCP_ENDPOINT, headers=HEADERS, json=payload, timeout=45)
    
    if response.status_code != 200:
        print(f"❌ MCP Call Error {response.status_code}: {response.text}")
        return None

    try:
        return response.json()
    except Exception:
        return {"result": {"content": [{"type": "text", "text": response.text}]}}


def run_agentic_heatmap_workflow():
    """
    Executes an autonomous two-step tool chain:
    Step 1: Calls the 'heatmap' tool.
    Step 2: Captures the 'activity_id' / 'heatmap_id'.
    Step 3: Loops using the 'heatmap_read' tool until completion.
    """
    print("=== Agentic Workflow Started: Urban Heatmap Analysis ===")
    
    # 1. Step 1: Agent decides to invoke the heatmap tool
    heatmap_args = {
        "polygon_aoi": {
            "type": "Polygon",
            "coordinates": [[
                [-74.0170, 40.7051],
                [-74.0031, 40.7051],
                [-74.0031, 40.7180],
                [-74.0170, 40.7180],
                [-74.0170, 40.7051]
            ]]
        },
        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1
        },
        "granularity": 100,
        "wait_for_completion": False  # Force asynchronous multi-turn test
    }

    resp1 = mcp_call_tool("heatmap", heatmap_args, request_id=10)
    if not resp1:
        return

    # Extract text content or result data from MCP response structure
    result_block = resp1.get("result", {})
    content_items = result_block.get("content", [])
    
    raw_text = ""
    for item in content_items:
        if item.get("type") == "text":
            raw_text += item.get("text", "")

    print(f"📥 Tool 'heatmap' Raw Output:\n{raw_text}\n")

    # Try to extract an activity_id or heatmap_id from the text response
    # (If the agent receives an ID, it proceeds to step 2)
    activity_id = None
    try:
        parsed_data = json.loads(raw_text)
        activity_id = parsed_data.get("data", {}).get("activity_id") or parsed_data.get("heatmap_id")
    except Exception:
        # Fallback search if plain text contains ID format
        import re
        match = re.search(r'(?:activity_id|heatmap_id)[:=]\s*["\']?([a-zA-Z0-9\-_]+)', raw_text)
        if match:
            activity_id = match.group(1)

    if not activity_id:
        print("⚠️ [Agent Notice] No explicit activity ID parsed or job completed synchronously.")
        print("   Full Result:", result_block)
        return

    print(f"🔍 [Agent Intelligence] Captured Asynchronous Identifier: {activity_id}")
    print("🔄 [Agent Action] Switching to polling tool: 'heatmap_read'...\n")

    # 2. Step 2: Agent chains the read tool in a loop
    read_url_slug = activity_id
    for attempt in range(1, 25):
        time.sleep(5)
        
        # Note: Depending on tool schema, parameter name may be heatmap_id or activity_id
        read_args = {"heatmap_id": read_url_slug}
        resp2 = mcp_call_tool("heatmap_read", read_args, request_id=20 + attempt)
        
        read_result_block = resp2.get("result", {})
        read_text = "".join([i.get("text", "") for i in read_result_block.get("content", [])])
        
        print(f"   [Polling Attempt {attempt:02d}] Read Output snippet: {read_text[:120]}...")

        if "Completed" in read_text or "stats_data" in read_text or "succeeded" in read_text.lower():
            print("\n🎉 Agent successfully completed tool chain!")
            print(f"Final Data:\n{read_text}")
            break
        elif "Failed" in read_text:
            print("\n❌ Agent detected terminal failure state in tool output.")
            break


if __name__ == "__main__":
    if API_KEY == "PASTE_YOUR_API_KEY_HERE":
        print("⚠️ Please configure your FORTYGUARD_API_KEY before running Module 4.")
    else:
        run_agentic_heatmap_workflow()