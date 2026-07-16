
import json
from dotenv import load_dotenv
import os
from enum import Enum
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Optional
from langchain_openai import ChatOpenAI


load_dotenv()  # Load environment variables from .env file

llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct",
    base_url="http://localhost:30000/v1",
    api_key="EMPTY"
)


class SeriousnessAssessment(str, Enum):
    SERIOUS = "Serious"
    NON_SERIOUS = "Non-Serious"


class CausalityAssessment(str, Enum):
    CERTAIN = "Certain"
    PROBABLE = "Probable"
    POSSIBLE = "Possible"
    UNLIKELY = "Unlikely"
    UNASSESSEABLE = "Unassessable"


class LabelingStatus(str, Enum):
    EXPECTED = "Expected"
    UNEXPECTED = "Unexpected"
    UNKNOWN = "Unknown"


class MedicalReview(BaseModel):
    review_summary: str = Field(
        description="A detailed medical review of the case. Make the content detailed enough to represent all the nuances of the case. Generate synthetic cross reference information from Drug Database. Make this section information rich so that it can be used to generate the rest of the information generated. Make synthetic data about information about the patient's medical history, laboratory values, and other potential risk factors where needed."\
    )
    
    meddra_pt: str = Field(
        description="MedDRA Preferred Term (PT) for the adverse event."
    )

    meddra_soc: str = Field(
        description="MedDRA System Organ Class (SOC) corresponding to the PT."
    )

    primary_event: str = Field(
        description="Primary adverse event considered most clinically relevant."
    )

    secondary_events: str = Field(
        description="Additional reported adverse events."
    )
    
    seriousness_assessment: SeriousnessAssessment = Field(
        description="Assessment of whether the adverse event is serious."
    )

    seriousness_rationale: str = Field(
        description="Justification for the seriousness assessment."
    )

    causality_assessment: CausalityAssessment = Field(
        description="Relationship between suspect drug and adverse event."
    )

    causality_rationale: str = Field(
        description="Justification for the causality assessment."
    )

    labeling_status: LabelingStatus = Field(
        description="Whether the event is expected according to product labeling."
    )

    labeling_rationale: str = Field(
        description="Justification for the labeling assessment."
    )

    review_confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1."
    )

    




def generate_synthetic_review(case_data):
    input_variables = ["case_data"]
    prompt = PromptTemplate.from_template("""
You are an experienced medical reviewer. You are generating training data for fine tuning an LLM model to predict these values based on case data.

Given the following adverse event case:

{case_data}

Generate a JSON object with exactly these fields:

{{
  "review_summary": "A detailed medical review of the case. Make the content detailed enough to represent all the nuances of the case. Generate synthetic cross reference information from Drug Database. Make this section information rich so that it can be used to generate the rest of the information generated. Make synthetic data where needed.",
  "meddra_pt": "MedDRA Preferred Term (PT) for the adverse event.",
  "meddra_soc": ""MedDRA System Organ Class (SOC) corresponding to the PT.",
  "primary_event":"Primary adverse event considered most clinically relevant.",
  "secondary_event":"Additional reported adverse events."",
  "seriousness_assessment": "Assessment of whether the adverse event is serious.",
  "seriousness_rationale": "Assessment of whether the adverse event is serious.",
  "causality_assessment": "Relationship between suspect drug and adverse event.",
  "causality_rationale": "Justification for the causality assessment.",
  "labeling_status": "Whether the event is expected according to product labeling.",
  "labeling_rationale": "Justification for the labeling assessment.",
  "review_confidence_score":"Confidence score between 0 and 1."
}}

Rules:
- Return JSON only.
- Do not invent demographics.
- Do not invent dates.
- Do not invent laboratory values.
- If information is unavailable, explain uncertainty.
- seriousness_assessment: Serious or Non-Serious
- causality_assessment: Certain, Probable, Possible, Unlikely, Unassessable
- labeling_status: Expected, Unexpected, Unknown
""")
    # print(prompt.invoke({"case_data":json.dumps(case_data, indent=2)}))
    
    structured_llm = llm.with_structured_output(MedicalReview)

    chain = prompt | structured_llm

    result = chain.invoke(
        {"case_data":json.dumps(case_data, indent=2)}
    )

    return json.loads(result.model_dump_json())



# generated_review = generate_synthetic_review({'report_id': '26220419', 'literature': None, 'serious': True, 'age': '58', 'drugs': [{'active_substance': 'VALACYCLOVIR HYDROCHLORIDE', 'drug_characterization': 'Suspect Drug', 'drug_name': 'VALACYCLOVIR HYDROCHLORIDE'}, {'active_substance': 'ZOLEDRONIC ACID', 'drug_characterization': 'Suspect Drug', 'drug_name': 'ZOMETA'}, {'active_substance': 'ACYCLOVIR', 'drug_characterization': 'Suspect Drug', 'drug_name': 'ACYCLOVIR'}, {'drug_name': 'MELPHALAN HYDROCHLORIDE', 'drug_characterization': 'Suspect Drug', 'active_substance': 'MELPHALAN HYDROCHLORIDE'}, {'drug_characterization': 'Secondary Suspect Drug', 'active_substance': None, 'drug_name': 'PIPERACILLINE TAZOBACTAM VIATRIS 4 g/0,5 g, poudre pour solution pour'}, {'active_substance': 'FLUCONAZOLE', 'drug_name': 'FLUCONAZOLE', 'drug_characterization': 'Suspect Drug'}], 'reactions': [{'reaction_name': 'C-reactive protein increased', 'outcome': 'Recovering/Resolving'}]})
# print(json.dumps(generated_review, indent=2))

#save json to file
