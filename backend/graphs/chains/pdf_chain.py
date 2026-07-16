from langchain_community.document_loaders import PDFMinerLoader
from langchain_core.runnables import RunnableLambda
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from llm import llm

# llm = ChatGroq(
#     model="meta-llama/llama-4-scout-17b-16e-instruct"
# )


def load_pdf(data):

    loader = PDFMinerLoader(
        data["pdf_path"]
    )

    docs = loader.load()

    text = "\n".join(
        doc.page_content
        for doc in docs
    )

    return {
        "pdf_text": text
    }


pdf_loader = RunnableLambda(load_pdf)


def analyze_pdf(data):

    response = llm.invoke(
        [
            HumanMessage(
                content=f"""
Analyze this medical report.

Extract:
- Patient demographics
- Diagnoses
- Medications
- Clinical findings
- Follow-up recommendations

Report:

{data["pdf_text"]}
"""
            )
        ]
    )

    return {
        "summary": response.content
    }


analyzer = RunnableLambda(analyze_pdf)

pdf_chain = pdf_loader | analyzer