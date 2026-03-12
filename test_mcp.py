import asyncio
from agno.tools.mcp import MCPTools

async def main():
    mcp = MCPTools(transport='streamable-http', url='https://pillbin-mcp-server-f7c6fyfcctgqb7ec.canadacentral-01.azurewebsites.net/mcp')
    await mcp.__aenter__()
    print("Initialized check!")
    print(mcp.get_functions())
    await mcp.__aexit__(None, None, None)

asyncio.run(main())
