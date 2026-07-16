from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel,Field
from typing import List,Dict
from llm import llm

class Diseases(BaseModel):
    list_of_diseases: List[str]



pydantic_parser = RunnableLambda(lambda x:x.model_dump())
extract_list_of_diseases = RunnableLambda(lambda x:x['list_of_diseases'])
extract_list_of_symptoms = RunnableLambda(lambda x:x['list_of_symptoms'])
list_to_string = RunnableLambda(lambda x: ', '.join(x))




disease_prompt = ChatPromptTemplate.from_template("""

You are given a patient summary: {patient_summary}
                            
Based on the patient summary compute a list of diseases described in the patient summary to compute Symptoms.

                            """)


structured_llm = llm.with_structured_output(Diseases)


disease_computation_chain = disease_prompt | structured_llm | pydantic_parser | extract_list_of_diseases



# result = chain.invoke({
#     "patient_summary": "The patient, a 37-year-old, experienced a fatal overdose while taking multiple suspect drugs, including methylphenidate, budesonide, metoprolol, esomeprazole magnesium/naproxen, valsartan, clonazepam, esomeprazole magnesium, metformin, sertraline hydrochloride, amlodipine besylate, symbicort, fentanyl, budesonide/formoterol fumarate, methadone, and hydrochlorothiazide/valsartan."
# })


# print(result)
