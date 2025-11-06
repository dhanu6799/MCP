import os
from dotenv import load_dotenv

load_dotenv(override=True)

brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}

# MCP servers for job tracker: Jobs API, Push Notifications
tracker_mcp_server_params = [
    {"command": "uv", "args": ["run", "jobs_server.py"]},
    {"command": "uv", "args": ["run", "push_server.py"]},
]

# MCP servers for researcher: Fetch, Brave Search, Memory
def researcher_mcp_server_params(name: str):
    return [
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,
        },
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
        },
    ]