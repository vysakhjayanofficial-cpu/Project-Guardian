from typing import TypedDict,List,Dict

from langgraph.graph import StateGraph, START, END
from graphs.chains.compute_diseases import disease_computation_chain
from graphs.chains.compute_symptoms import symptoms_computation_chain
from graphs.chains.compute_symptom_match import symptom_match_chain


class DiseaseState(TypedDict):
    patient_summary: str
    list_of_diseases: List[str]
    symptoms: Dict[str,List[str]]
    symptom_match: Dict[str,float]


def compute_symptomps(state: DiseaseState):

    patient_summary = state["patient_summary"]

    list_of_diseases = disease_computation_chain.invoke({"patient_summary": patient_summary})

    symptomps = {disease: symptoms_computation_chain.invoke({"disease": disease}) for disease in list_of_diseases}

    symptom_match = {disease: symptom_match_chain.invoke({"patient_summary": patient_summary, "list_of_symptoms": ",".join(symptomps[disease])}) for disease in list_of_diseases}

    return {"list_of_diseases": list_of_diseases, "symptoms": symptomps, "symptom_match": symptom_match}






builder = StateGraph(DiseaseState)

builder.add_node("compute_symptomps", compute_symptomps)
builder.add_edge(START, "compute_symptomps")
builder.add_edge("compute_symptomps", END)

summary_graph = builder.compile()