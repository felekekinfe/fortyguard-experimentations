"""
Module 3: Deep-Dive MCP Protocol Inspection (JSON-RPC over Streamable HTTP)
--------------------------------------------------------------------------
This script bypasses IDE wrappers and communicates directly with FortyGuard's
remote MCP server using raw JSON-RPC 2.0 messages over HTTP POST.
"""

os = __import__("os")
json = __import__("json")
requests = __import__("requests")

# Remote MCP Endpoint provided in FortyGuard's documentation
MCP_ENDPOINT = "https://tos-mcp.app.fortyguard.com/mcp"

# Note: FortyGuard's MCP server uses Bearer auth (unlike their REST API which uses 'api-key')
API_KEY = os.getenv("FORTYGUARD_API_KEY", "PASTE_YOUR_API_KEY_HERE")

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Authorization": f"Bearer {API_KEY}"
}

def send_json_rpc(method: str, params: dict = None, request_id: int = 1):
    """Sends a raw JSON-RPC 2.0 payload to the remote MCP HTTP endpoint."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": request_id
    }
    if params is not None:
        payload["params"] = params

    print(f"🔌 [JSON-RPC Request] Method: {method}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(MCP_ENDPOINT, headers=HEADERS, json=payload, timeout=30)
    
    print(f"   HTTP Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ MCP Transport Error: {response.text}")
        return None

    # Streamable HTTP can return application/json or text/event-stream chunks
    try:
        return response.json()
    except Exception:
        print("   [Info] Response received as text/event-stream or raw stream.")
        return response.text


def inspect_mcp_server():
    """Performs the MCP handshake and lists all available tools."""
    
    # Step 1: Initialize Session / Handshake
    init_params = {
        "protocolVersion": "2025-11-25",
        "capabilities": {},
        "clientInfo": {
            "name": "fortyguard-evaluation-client",
            "version": "1.0.0"
        }
    }
    
    print("=== Step 1: MCP Initialization Handshake ===")
    init_result = send_json_rpc("initialize", init_params, request_id=1)
    print("📥 Handshake Response:")
    print(json.dumps(init_result, indent=2) if isinstance(init_result, dict) else init_result)
    print("\n" + "="*50 + "\n")

    # Step 2: Tool Discovery (tools/list)
    print("=== Step 2: Discovering Tools (tools/list) ===")
    tools_result = send_json_rpc("tools/list", {}, request_id=2)
    
    if isinstance(tools_result, dict) and "result" in tools_result:
        tools = tools_result["result"].get("tools", [])
        print(f"✅ Discovered {len(tools)} tools on FortyGuard MCP Server:\n")
        for idx, tool in enumerate(tools, 1):
            print(f"   {idx}. Name: {tool.get('name')}")
            print(f"      Description: {tool.get('description', '')[:90]}...")
            schema_props = tool.get('inputSchema', {}).get('properties', {})
            print(f"      Parameters: {list(schema_props.keys())}\n")
    else:
        print("Raw Tools Response:", tools_result)


if __name__ == "__main__":
    print("=== FortyGuard Module 3 Test: Raw MCP Inspection ===")
    if API_KEY == "PASTE_YOUR_API_KEY_HERE":
        print("⚠️ Warning: Please set your FORTYGUARD_API_KEY environment variable.")
    inspect_mcp_server()