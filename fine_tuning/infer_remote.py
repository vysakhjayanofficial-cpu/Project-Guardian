from openai import OpenAI
import json

client = OpenAI(
    base_url="http://localhost:30005/v1",
    api_key="dummy"  # vLLM doesn't require a real key by default
)

response = client.completions.create(
    model="./qwen_merged",
    prompt="""
Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are a medical review assistant. You will be given a summary of a medical review and you need to provide JSON formmat output that includes the following information:
1 . "meddra_pt": the preferred term of the medical event
2. "meddra_soc": the system organ class of the medical event
3. "primary_event": the primary adverse event reported
4. "secondary_events": the secondary adverse events reported
5. "seriousness_assessment": the seriousness assessment of the medical event
6. "seriousness_rationale": the rationale for the seriousness assessment
7. "causality_assessment": the causality assessment of the medical event
8. "causality_rationale": the rationale for the causality assessment
9. "labeling_status": the labeling status of the medical event
10. "labeling_rationale": the rationale for the labeling status
11. "review_confidence_score": the confidence score of the review.

Rules:
- Return JSON only.
- Do not invent demographics.
- Do not invent dates.
- Do not invent laboratory values.
- If information is unavailable, explain uncertainty.

### Input:
Kimberly Lawrence, 46, is being treated for Type 2 Diabetes Mellitus and Peripheral Neuropathy. She is on Metformin, Gabapentin, Atorvastatin, Lisinopril, Vitamin B12, and Aspirin. Atorvastatin's side effects include gastrointestinal issues, dermatological reactions, neurological symptoms, musculoskeletal problems, cardiovascular risks, respiratory conditions, genitourinary issues, hepatic complications, immunological reactions, endocrine disorders, hematological effects, ophthalmological concerns, and psychological impacts. Her condition is stable with controlled blood sugar and neuropathy symptoms. Follow-up in 3 months for HbA1c and CMP monitoring.

### Response:
""",
    max_tokens=512,
    temperature=0.0,
)

print(response.choices[0].text)
print(json.loads(response.choices[0].text))
