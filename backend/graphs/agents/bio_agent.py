from langchain.agents import create_agent
from llm import llm
from pydantic import BaseModel
from graph.chains.symptom_analysis import chain

class Answer(BaseModel):
    summary: str
    confidence: float


agent = create_agent(
    model=llm,
    tools = [],
    system_prompt="You are a bio medical analyst. Based on patient summary convert ",
    response_format=Answer

)

result = agent.invoke({"messages": [{"role": "system", "content": "Simulate BioMistral model and provide information regarding medical queries."},
                                    {"role": "user", "content": "Summarize AI trends in a few sentences."}]})
print(result["structured_response"].model_dump())