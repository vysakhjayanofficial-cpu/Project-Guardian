import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def main():
    client = MultiServerMCPClient(
        {
            "medical": {
                "command": "python",
                "args": ["./MCP/pubmed-mcp/server.py"],
                "transport": "stdio",
            }
        }
    )

    tools = await client.get_tools()

    for tool in tools:
        print(tool.name)

asyncio.run(main())