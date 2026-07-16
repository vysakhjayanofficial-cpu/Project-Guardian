
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


load_dotenv()

llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct",
    base_url="http://localhost:30000/v1",
    api_key="EMPTY"
)

if __name__ == "__main__":
    print(llm.invoke("Hello").content)