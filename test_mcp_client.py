"""Talk to server.py the way an MCP client does: start it, list what it offers, call it."""
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CASE = ("Work orders are not syncing to the mobile app, error ERR-1138. "
        "Reach me at ravi.ivanov@example.com or (425) 555-0163.")


async def main():
    params = StdioServerParameters(command=sys.executable, args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("tools:    ", [t.name for t in tools.tools])
            templates = await session.list_resource_templates()
            print("resources:", [t.uriTemplate for t in templates.resourceTemplates])
            prompts = await session.list_prompts()
            print("prompts:  ", [p.name for p in prompts.prompts])
            print()

            result = await session.call_tool("redact_text", {"text": CASE})
            print("redact_text  ->", result.content[0].text)

            result = await session.call_tool("classify_case", {"text": CASE})
            print("classify_case->", result.content[0].text)

            result = await session.call_tool("search_kb", {"query": "work orders not syncing mobile app"})
            print("search_kb    ->", result.content[0].text)

            article = await session.read_resource("kb://article/D365-1")
            print("resource     ->", article.contents[0].text)


asyncio.run(main())