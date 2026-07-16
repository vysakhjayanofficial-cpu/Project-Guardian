from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel,Field
from typing import List,Dict
from llm import llm


class Symptomps(BaseModel):
    list_of_symptoms: List[str] = Field(description="Computed symptoms for detected diseases with value.")


pydantic_parser = RunnableLambda(lambda x:x.model_dump())
extract_list_of_symptoms = RunnableLambda(lambda x:x['list_of_symptoms'])
list_to_string = RunnableLambda(lambda x: ', '.join(x))




symptomps_prompt = ChatPromptTemplate.from_template("""

You are given the name of a disease: {disease}
Compute a list of symptoms for the disease.
                                                    
Always return a list of values only.
                                                    
""")

symptomps_llm = llm.with_structured_output(Symptomps)


symptoms_computation_chain = symptomps_prompt | symptomps_llm | pydantic_parser| extract_list_of_symptoms



