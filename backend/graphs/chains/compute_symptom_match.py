from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel,Field
from typing import List,Dict
from llm import llm

class Symptom_Match(BaseModel):
    symptom_match: float



pydantic_parser = RunnableLambda(lambda x:x.model_dump())
extract_percentage = RunnableLambda(lambda x:x['symptom_match'])
list_to_string = RunnableLambda(lambda x: ', '.join(x))




symptom_match_prompt = ChatPromptTemplate.from_template("""

You are given a list of symptoms and patient summary
                                                        
Symptomps: {list_of_symptoms}
Patient Summary:{patient_summary}
                            
Based on the patient summary create a floating point number from 0-100. Representing what percentage of those symptomps detected in the patient summary.
                            """)


structured_llm = llm.with_structured_output(Symptom_Match)


symptom_match_chain = symptom_match_prompt | structured_llm | pydantic_parser | extract_percentage

