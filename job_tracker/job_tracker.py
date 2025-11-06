from contextlib import AsyncExitStack
from tracers import make_trace_id
from agents import Agent, Tool, Runner, trace
from dotenv import load_dotenv
import os
from agents.mcp import MCPServerStdio
from templates import (
    researcher_instructions,
    tracker_instructions,
    tracking_message,
    research_tool,
)
from mcp_params import tracker_mcp_server_params, researcher_mcp_server_params
from job_client import read_tracker_resource, read_category_resource

load_dotenv(override=True)

MAX_TURNS = 30


async def get_researcher(mcp_servers) -> Agent:
    researcher = Agent(
        name="JobResearcher",
        instructions=researcher_instructions(),
        model="gpt-4o-mini",
        mcp_servers=mcp_servers,
    )
    return researcher


async def get_researcher_tool(mcp_servers) -> Tool:
    researcher = await get_researcher(mcp_servers)
    return researcher.as_tool(
        tool_name="JobResearcher", 
        tool_description=research_tool()
    )


class JobTracker:
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.agent = None

    async def create_agent(self, tracker_mcp_servers, researcher_mcp_servers) -> Agent:
        tool = await get_researcher_tool(researcher_mcp_servers)
        self.agent = Agent(
            name=self.name,
            instructions=tracker_instructions(self.name, self.category),
            model="gpt-4o-mini",
            tools=[tool],
            mcp_servers=tracker_mcp_servers,
        )
        return self.agent

    async def get_tracker_report(self) -> str:
        return await read_tracker_resource(self.name)

    async def run_agent(self, tracker_mcp_servers, researcher_mcp_servers):
        self.agent = await self.create_agent(tracker_mcp_servers, researcher_mcp_servers)
        tracker_data = await self.get_tracker_report()
        category_info = await read_category_resource(self.category)
        message = tracking_message(self.name, self.category, tracker_data, category_info)
        await Runner.run(self.agent, message, max_turns=MAX_TURNS)

    async def run_with_mcp_servers(self):
        async with AsyncExitStack() as stack:
            tracker_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in tracker_mcp_server_params
            ]
            async with AsyncExitStack() as stack:
                researcher_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self.run_agent(tracker_mcp_servers, researcher_mcp_servers)

    async def run_with_trace(self):
        trace_name = f"{self.name}-job-tracking"
        trace_id = make_trace_id(f"{self.name.lower()}")
        with trace(trace_name, trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running job tracker {self.name}: {e}")