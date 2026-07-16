# from graphs.chains.symptom_analysis import symptoms_computation_chain

# from graphs.graphs.symptom_analysis_graph import summary_graph



# result = summary_graph.invoke({
#     "patient_summary": "The patient, a 37-year-old, experienced a fatal overdose while taking multiple suspect drugs, including methylphenidate, budesonide, metoprolol, esomeprazole magnesium/naproxen, valsartan, clonazepam, esomeprazole magnesium, metformin, sertraline hydrochloride, amlodipine besylate, symbicort, fentanyl, budesonide/formoterol fumarate, methadone, and hydrochlorothiazide/valsartan."
# })


# print(result)

from graphs.chains.image_chain import image_chain
from dotenv import load_dotenv

load_dotenv()
result = image_chain.invoke({"image_path": "./sample_files/Xray.png"})

print(result)


# from graphs.chains.pdf_chain import pdf_chain

# result = pdf_chain.invoke({"pdf_path":"./sample_files/PDF_Deid_Deidentification_0.pdf"})

# print(result)

# from graphs.graphs.patient_summary_graph import summary_graph


# result = summary_graph.invoke({"patient_summary": """Kimberly Lawrence is a 46-year-old female diagnosed with Type 2 Diabetes Mellitus and
# Peripheral Neuropathy. Current management focuses on glycemic control through
# medication and lifestyle adjustments. Overall health status is stable.""",
#     "patient_id":"PAT-E0EB6E"})


# print(result)
# import asyncio
# from graphs.agents.pub_med_agent import run_research

# async def main():
#     summary = """
#     A patient receiving amoxicillin developed a widespread pruritic rash two days after starting therapy. The rash improved after discontinuation of amoxicillin and treatment with antihistamines. No hospitalization was required. No other adverse events were reported. The reviewer considered the event likely related to amoxicillin. Rash is a known adverse reaction listed in the product labeling.
#     """
#     response = await run_research(patient_summary=summary)
#     print(response)

# asyncio.run(main())

# from graphs.graphs.sider_rag_graph import sider_graph


# result = sider_graph.invoke({"query": "What are the side effects of 18F-flutemetamol and hydroxyprogesterone?"})

# print("\n--- GENERATED ANSWER ---")
# print(result["generation"])
# print("------------------------\n")
