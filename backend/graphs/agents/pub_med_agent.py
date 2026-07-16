from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from llm import llm

SYSTEM_PROMPT = """
You are an expert medical researcher.
Your job is to conduct research on PubMed articles and use them to find
suitable PubMed articles based on the patient summary.
Output SHOULD BE a list of valid PubMed articles with a one liner
regarding that article and their links in an ordered list.
You have access to PubMed MCP tools as your primary means of gathering
information.
Output Format:
1. Article Title 1: Link to Article 1 (One-liner summary)
2. Article Title 2: Link to Article 2 (One-liner summary)
...
"""

async def pub_med_agent_main(patient_summary: str) -> str:
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
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT
    )

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
Find suitable PubMed articles for the following patient summary.
Patient Summary:
{patient_summary}
"""
                }
            ]
        }
    )

    # The final AI message in the messages list contains the answer
    final_message = result["messages"][-1]
    return final_message.content

run_research = pub_med_agent_main