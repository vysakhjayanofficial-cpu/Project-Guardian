import os
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict
from llm import llm

class Symptomps(BaseModel):
    list_of_symptoms: List[str] = Field(description="Computed symptoms for detected diseases with value.")

pydantic_parser = RunnableLambda(lambda x: x.model_dump() if hasattr(x, 'model_dump') else x)
extract_list_of_symptoms = RunnableLambda(lambda x: x.get('list_of_symptoms', []))
list_to_string = RunnableLambda(lambda x: ', '.join(x))

# Prompt instructing BioMistral to return plain symptoms list
biomistral_prompt = ChatPromptTemplate.from_template("""
You are a medical analyst.
Disease Name: {disease}
Provide a list of common symptoms for this disease. 
List each symptom on a new line. Do not include any conversational text or explanation.
""")

# Main LLM structured prompt fallback
main_llm_prompt = ChatPromptTemplate.from_template("""
You are given the name of a disease: {disease}
Compute a list of symptoms for the disease.
""")

def parse_symptoms_text(output_text: str) -> Dict[str, List[str]]:
    """Clean and parse BioMistral free text outputs into structured symptoms."""
    lines = output_text.splitlines()
    symptoms = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Strip bullets (- * +), numbering (1. 2. 1) etc.
        cleaned = re.sub(r'^(\d+[\.\)]|\-|\*|\+)\s*', '', line).strip()
        # Strip JSON bracket artifacts if model attempts JSON output
        cleaned = cleaned.replace('[', '').replace(']', '').replace('"', '').replace("'", "").replace(',', '')
        if cleaned:
            # Handle inline comma lists
            parts = [p.strip() for p in cleaned.split(',') if p.strip()]
            symptoms.extend(parts)
            
    # Deduplicate and capitalize
    unique_symptoms = list(dict.fromkeys([s.lower() for s in symptoms if len(s) > 1]))
    unique_symptoms = [s.capitalize() for s in unique_symptoms]
    
    return {"list_of_symptoms": unique_symptoms}

# Initialize BioMistral model
biomistral_llm = None

# Option 1: Try connecting to local vLLM API server at port 30000 serving BioMistral
try:
    from langchain_openai import ChatOpenAI
    biomistral_llm = ChatOpenAI(
        base_url="http://localhost:30006/v1",
        api_key="dummy",
        model="./biomistral",
        temperature=0.0
    )
    # Check if port 30000 is open by attempting call
    biomistral_llm.invoke("Hi")
    print("Successfully connected to BioMistral API server on port 30006.")
except Exception as e:
    print(f"Could not connect to BioMistral API server: {e}. Trying local loading...")
    biomistral_llm = None

# Option 2: Fallback to local Hugging Face pipeline if model files exist
if biomistral_llm is None:
    model_path = "./biomistral"
    if os.path.exists(model_path):
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            from langchain_huggingface import HuggingFacePipeline
            
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(model_path)
            pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=256)
            biomistral_llm = HuggingFacePipeline(pipeline=pipe)
            print("Successfully loaded BioMistral from local HF model directory.")
        except Exception as hf_err:
            print(f"Failed to load BioMistral from local HF folder: {hf_err}")
            biomistral_llm = None

# Option 3: Fallback to main LLM if BioMistral is not available
if biomistral_llm is None:
    print("BioMistral model not found or failed to load. Falling back to the main LLM.")
    symptomps_llm = llm.with_structured_output(Symptomps)
    symptoms_computation_chain = main_llm_prompt | symptomps_llm | pydantic_parser | extract_list_of_symptoms
else:
    # Build text completion chain for BioMistral
    symptoms_computation_chain = biomistral_prompt | biomistral_llm | StrOutputParser() | RunnableLambda(parse_symptoms_text) | extract_list_of_symptoms
