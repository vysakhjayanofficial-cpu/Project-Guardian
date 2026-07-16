from typing import TypedDict,List,Dict
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from graphs.chains.image_chain import image_chain
from graphs.chains.pdf_chain import pdf_chain
from graphs.graphs.sider_rag_graph import sider_graph
from llm import llm
from pydantic import BaseModel,Field
from langchain_core.prompts import ChatPromptTemplate
class MedicalSummary(BaseModel):
    patient_summary: str = Field(description="Patient summary for analysis by the doctor. Include the details of current medications and their side effects. MAX WORD LIMIT: 256")
    current_medications: List[str] = Field(description="Current medications detected in patient summary, ONLY include the medicine name.")
    current_ailment: List[str] = Field(description="Current ailments detected in patient summary, ONLY include the disease name.")
    
def get_file_type(path: str) -> str:
    ext = Path(path).suffix.lower()

    if ext == ".pdf":
        return "pdf"

    if ext in {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".gif",
        ".webp",
        ".tiff"
    }:
        return "image"
    return "unknown"

class PatientSummaryState(TypedDict):
    patient_summary: str
    patient_id: str
    multimodal_articles: List[str]
    current_medications: List[str]
    current_ailment: List[str]


def populate_reports(state: PatientSummaryState):
    patient_asset_path = Path(f"./patient_assets/{state['patient_id']}")
    multimodal_articles = [str(p) for p in patient_asset_path.glob("*")]
    return {"multimodal_articles": multimodal_articles}

def process_multimodal_articles(state: PatientSummaryState):
    try:
        with open(f"./patient_assets/{state['patient_id']}/global_data.txt", "r", encoding="utf-8") as f:
            GLOBAL_DATA_OBJECT = f.read()
    except:
        GLOBAL_DATA_OBJECT = f"{state['patient_summary']}"
    multimodal_articles = state["multimodal_articles"]
    for article in multimodal_articles:
        file_type = get_file_type(article)
        if file_type == "image":
            data = image_chain.invoke({"image_path": article})
            GLOBAL_DATA_OBJECT = GLOBAL_DATA_OBJECT + data["summary"]
        elif file_type == "pdf":
            data = pdf_chain.invoke({"pdf_path": article})
            GLOBAL_DATA_OBJECT = GLOBAL_DATA_OBJECT + data["summary"]
        else:
            pass
    #Save GLOBAL_DATA_OBJECT
    with open(f"./patient_assets/{state['patient_id']}/global_data.txt", "w", encoding="utf-8") as f:
        f.write(GLOBAL_DATA_OBJECT)


def summarize_patient_data(state: PatientSummaryState):
    try:
        with open(f"./patient_assets/{state['patient_id']}/global_data.txt", "r", encoding="utf-8") as f:
            GLOBAL_DATA_OBJECT = f.read()
    except:
        GLOBAL_DATA_OBJECT = f"{state['patient_summary']}"

    SIDER_query = llm.invoke(f"""

Given the patient summary, generate a text query for RAG search on side effect context from SIDER database. ONLY include the details of the drugs in the query.
Include details of all the medicines patient consumed in the query. Return ONLY the query.
                             
<patient_summary>
{GLOBAL_DATA_OBJECT}
</patient_summary>
                             



                             """)
    print(SIDER_query.content)
    SIDER_data = sider_graph.invoke({"query": SIDER_query.content})
    print(SIDER_data["generation"])

    doctor_summary_prompt = ChatPromptTemplate.from_template("""

    You are given a detailed patient summary notes and the side effect details of medicines consumed directly from SIDER database.
                                                            
    Patient Summary:{patient_summary}
                                                             
    Side Effect details: {side_effect_details}

                                                             
                                
    Based on the patient summary create the following pieces of information
                                                             
    - Patient Summary: Patient summary for analysis by the doctor. Include the details of current medications and their side effects. MAX WORD LIMIT: 256
    - Current Medications: Current medications detected in the patient summary. ONLY include the medicine name.
    - Current Ailments: Current ailments detected in the patient summary, ONLY include the disease name.
                                """)
    
    structured_llm = llm.with_structured_output(MedicalSummary)
    
    doctor_summary_chain = doctor_summary_prompt | structured_llm

    summary_object = doctor_summary_chain.invoke({
        "patient_summary": GLOBAL_DATA_OBJECT,
        "side_effect_details": SIDER_data["generation"]
    }).model_dump()
     
    
    return {"patient_summary": summary_object["patient_summary"],
            "current_medications": summary_object["current_medications"],
            "current_ailment": summary_object["current_ailment"]}



builder = StateGraph(PatientSummaryState)

builder.add_node("populate_reports", populate_reports)
builder.add_node("process_multimodal_articles", process_multimodal_articles)
builder.add_node("summarize_patient_data", summarize_patient_data)
builder.add_edge(START, "populate_reports")
builder.add_edge("populate_reports", "process_multimodal_articles")
builder.add_edge("process_multimodal_articles", "summarize_patient_data")
builder.add_edge("summarize_patient_data", END)

summary_graph = builder.compile()










