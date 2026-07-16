from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class ContactInfo(BaseModel):
    name: str = Field(description="The name of the person")
    email: str = Field(description="The email address of the person")
    phone: str = Field(description="The phone number of the person")

llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct",
    base_url="http://localhost:30000/v1",
    api_key="EMPTY"
)

structured_llm = llm.with_structured_output(ContactInfo)

result = structured_llm.invoke(
    "Extract contact info from: John Doe, john@example.com, (555) 123-4567"
)

print(result)