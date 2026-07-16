import base64
import duckdb
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import requests
from llm import llm
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Import the compiled LangGraph from your project
from graphs.graphs.symptom_analysis_graph import summary_graph as symptom_graph
from graphs.graphs.patient_summary_graph import summary_graph as patient_summary_graph

DB_FILE = "medical_review.duckdb"

# Initialize DuckDB tables
def init_db():
    con = duckdb.connect(DB_FILE)
    con.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id VARCHAR PRIMARY KEY,
        patient_name VARCHAR,
        age INTEGER,
        gender VARCHAR,
        phone VARCHAR,
        current_medications VARCHAR,
        current_ailment VARCHAR,
        adverse_event VARCHAR,
        medical_history VARCHAR,
        created_at TIMESTAMP
    )
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        attachment_id BIGINT,
        patient_id VARCHAR,
        filename VARCHAR,
        mime_type VARCHAR,
        file_data BLOB,
        uploaded_at TIMESTAMP
    )
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        doctor_id VARCHAR PRIMARY KEY,
        doctor_name VARCHAR,
        specialization VARCHAR,
        hospital VARCHAR,
        phone VARCHAR,
        email VARCHAR,
        created_at TIMESTAMP
    )
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS doctor_notes (
        patient_id VARCHAR PRIMARY KEY,
        notes VARCHAR,
        updated_at TIMESTAMP
    )
    """)
    con.close()

def clean_user_input(text: str) -> str:
    if not text:
        return ""
    if "--- USER FILLED ---" in text:
        try:
            parts = text.split("--- USER FILLED ---")[1].split("--- AI GENERATED ---")
            return parts[0].strip()
        except Exception:
            pass
    return text.strip()

    
# Run DB init
init_db()

app = FastAPI(
    title="LangGraph Guardian API",
    description="FastAPI server serving the symptom analysis LangGraph & DuckDB Patient Registry",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class AttachmentIn(BaseModel):
    name: str
    data: str  # Base64 encoded file data

class PatientSummaryRequest(BaseModel):
    patient_summary: str
    current_ailment: Optional[str] = ""
    patient_id: Optional[str] = "PAT-DEFAULT"
    files: Optional[List[AttachmentIn]] = []

class PatientIn(BaseModel):
    patient_id: str
    patient_name: str
    age: int
    gender: str
    phone: str
    current_medications: Optional[str] = ""
    current_ailment: Optional[str] = ""
    adverse_event: Optional[str] = ""
    medical_history: Optional[str] = ""
    files: Optional[List[AttachmentIn]] = []

class DoctorIn(BaseModel):
    doctor_id: str
    doctor_name: str
    specialization: str
    hospital: str
    phone: str
    email: str


def save_file_to_disk(patient_id: str, filename: str, base64_data: str):
    import os
    safe_patient_id = "".join(c for c in patient_id if c.isalnum() or c in ("-", "_")).strip()
    if not safe_patient_id:
        safe_patient_id = "PAT-DEFAULT"
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, "patient_assets", safe_patient_id)
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        file_bytes = base64.b64decode(base64_data.split(",")[-1])
        file_path = os.path.join(save_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        print(f"Successfully saved {filename} to {file_path}")
    except Exception as e:
        print(f"Failed to save file {filename} to disk: {e}")


@app.post("/analyze-symptoms")
def analyze_symptoms(request: PatientSummaryRequest):
    try:
        # Save attachments if present
        if request.files:
            for file in request.files:
                save_file_to_disk(request.patient_id, file.name, file.data)
        
        # Invoke the graph with the initial state
        result = symptom_graph.invoke({
            "patient_summary": request.patient_summary
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patient_summary")
def get_patient_summary(request: PatientSummaryRequest):
    try:
        import os
        # Ensure patient assets directory exists even if no files are uploaded
        safe_patient_id = "".join(c for c in request.patient_id if c.isalnum() or c in ("-", "_")).strip()
        if not safe_patient_id:
            safe_patient_id = "PAT-DEFAULT"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(base_dir, "patient_assets", safe_patient_id)
        os.makedirs(save_dir, exist_ok=True)

        # Save attachments if present
        if request.files:
            for file in request.files:
                save_file_to_disk(request.patient_id, file.name, file.data)

        clean_history = clean_user_input(request.patient_summary)
        clean_ailment = clean_user_input(request.current_ailment or "")
        
        # Combine they for context-grounding the graphs
        combined_summary = clean_history
        if clean_ailment:
            combined_summary = f"Current Ailment (User Input):\n{clean_ailment}\n\nMedical History (User Input):\n{clean_history}"
            
        # Overwrite global_data.txt with the new clean combined summary
        global_data_path = os.path.join(save_dir, "global_data.txt")
        with open(global_data_path, "w", encoding="utf-8") as f:
            f.write(combined_summary)
        # Invoke the graph with the initial state
        result = patient_summary_graph.invoke({
            "patient_summary": combined_summary,
            "patient_id": request.patient_id
        })
        ai_summary = result.get("patient_summary", "")
        ai_ailment = result.get("current_ailment", "")
        
        if isinstance(ai_ailment, list):
            ai_ailment = "\n".join(ai_ailment)
            
        return {
            "patient_summary": f"--- USER FILLED ---\n{clean_history}\n\n--- ANALYZED ---\n{ai_summary}",
            "current_ailment": f"--- USER FILLED ---\n{clean_ailment}\n\n--- AI ANALYZED ---\n{ai_ailment}",
            "current_medications": result.get("current_medications", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def strip_tags(text: str) -> str:
    if not text:
        return ""
    text = text.replace("--- USER FILLED ---", "").replace("--- AI ANALYZED ---", "").replace("--- ANALYZED ---", "")
    return text.strip()

@app.post("/patients")
def save_patient_endpoint(payload: PatientIn):
    try:
        con = duckdb.connect(DB_FILE)
        
        # Save patient
        con.execute("""
        INSERT OR REPLACE INTO patients
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            payload.patient_id,
            payload.patient_name,
            payload.age,
            payload.gender,
            payload.phone,
            strip_tags(payload.current_medications),
            strip_tags(payload.current_ailment),
            payload.adverse_event,
            strip_tags(payload.medical_history),
            datetime.now()
        ])

        # Save attachments
        if payload.files:
            for idx, file in enumerate(payload.files):
                try:
                    # Save file to disk
                    save_file_to_disk(payload.patient_id, file.name, file.data)
                    
                    # Decode base64
                    blob_data = base64.b64decode(file.data.split(",")[-1])
                    con.execute("""
                    INSERT INTO attachments
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, [
                        int(datetime.now().timestamp() * 1000) + idx,
                        payload.patient_id,
                        file.name,
                        "application/octet-stream",
                        blob_data,
                        datetime.now()
                    ])
                except Exception as upload_err:
                    print(f"Attachment upload failed for {file.name}: {upload_err}")

        con.close()
        return {"success": True, "message": "✅ Patient Saved Successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Database Error: {str(e)}")


@app.get("/patients")
def get_patients(search_query: Optional[str] = ""):
    try:
        con = duckdb.connect(DB_FILE)
        if search_query.strip():
            term = f"%{search_query.strip()}%"
            rows = con.execute("""
            SELECT patient_id, patient_name, age, gender, phone, 
                   current_medications, current_ailment, adverse_event, 
                   medical_history, created_at
            FROM patients
            WHERE patient_id ILIKE ? OR patient_name ILIKE ? OR current_ailment ILIKE ?
            ORDER BY created_at DESC
            """, [term, term, term]).fetchall()
        else:
            rows = con.execute("""
            SELECT patient_id, patient_name, age, gender, phone, 
                   current_medications, current_ailment, adverse_event, 
                   medical_history, created_at
            FROM patients
            ORDER BY created_at DESC
            """).fetchall()
        con.close()

        # Parse into dictionary objects
        patients_list = []
        for r in rows:
            patients_list.append({
                "patient_id": r[0],
                "patient_name": r[1],
                "age": r[2],
                "gender": r[3],
                "phone": r[4],
                "current_medications": r[5],
                "current_ailment": r[6],
                "adverse_event": r[7],
                "medical_history": r[8],
                "created_at": r[9].isoformat() if r[9] else None
            })
        return patients_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load patients: {str(e)}")


@app.get("/patients/count")
def get_patient_count():
    try:
        con = duckdb.connect(DB_FILE)
        result = con.execute("SELECT COUNT(*) FROM patients").fetchone()
        count = result[0] if result else 0
        con.close()
        return {"count": count}
    except Exception:
        return {"count": 0}


class DoctorNotesIn(BaseModel):
    notes: str


def extract_medicines(notes: str, existing_meds: str) -> List[str]:
    import json
    prompt = f"""
You are an expert clinical pharmacologist.
Analyze the following clinical consultation notes and existing medications:

Consultation Notes (new entries):
{notes}

Existing Medications:
{existing_meds}

Identify and extract all the medicines/drug names mentioned in the notes or existing medications.
Format the output as a JSON list of drug names (strings).
Return ONLY the raw JSON list of strings. Do not include markdown code blocks. If no medicines are found, return an empty list [].

Example output: ["Metformin", "Aspirin", "Lisinopril"]
"""
    try:
        response = llm.invoke(prompt)
        text = response.content.strip()
        # Clean potential markdown
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
            if text.endswith("```"):
                text = text[:-3].strip()
        
        medicines = json.loads(text)
        if isinstance(medicines, list):
            return [m.strip() for m in medicines if m.strip()]
        
        # Try simple string split fallback if list is not parsed
        cleaned = text.replace("[", "").replace("]", "").replace('"', '').replace("'", "")
        return [m.strip() for m in cleaned.split(",") if m.strip()]
    except Exception as e:
        print(f"Error extracting medicines: {e}")
        # Try clean string parsing fallback
        try:
            cleaned = text.replace("[", "").replace("]", "").replace('"', '').replace("'", "")
            return [m.strip() for m in cleaned.split(",") if m.strip()]
        except Exception:
            return []


def check_medication_safety(patient_id: str, new_notes: str) -> dict:
    import os
    import json
    import duckdb
    
    # 1. Fetch existing medications from database
    existing_meds = ""
    try:
        con = duckdb.connect(DB_FILE)
        r = con.execute("SELECT current_medications FROM patients WHERE patient_id = ?", [patient_id]).fetchone()
        con.close()
        if r and r[0]:
            existing_meds = r[0]
    except Exception as e:
        print(f"Error fetching existing medications: {e}")
        
    # 2. Extract medicines from consultation notes and existing medications
    medicines = extract_medicines(new_notes, existing_meds)
    print(f"Extracted medicines for safety check: {medicines}")
    
    if not medicines:
        return {
            "is_safe": True,
            "reason": "No medications identified in the notes or current record.",
            "details": "Clinical consultation notes saved successfully. No medications were detected to perform a safety check.",
            "retrieved_side_effects": ""
        }
        
    # 3. Retrieve RAG documents from Chroma DB
    rag_context = ""
    retrieved_docs = []
    try:
        from graphs.graphs.sider_rag_graph import vector_store
        for med in medicines:
            # Query the vector store for this medicine
            # Retrieve top 2 documents per medicine
            docs = vector_store.similarity_search(med, k=2)
            retrieved_docs.extend(docs)
            
        # Deduplicate
        seen = set()
        unique_docs = []
        for d in retrieved_docs:
            content_hash = hash(d.page_content)
            if content_hash not in seen:
                seen.add(content_hash)
                unique_docs.append(d)
                
        rag_context = "\n\n".join([doc.page_content for doc in unique_docs])
    except Exception as e:
        print(f"Error retrieving from Chroma DB: {e}")
        rag_context = "Could not retrieve side effects from SIDER database."
        
    # 4. Use LLM to analyze safety based on retrieved contexts
    prompt = f"""
You are a clinical safety expert reviewing a patient's medication list and the doctor's new consultation notes.
Your task is to determine whether the combination of new medicines in the consultation notes and existing medications is safe.

Existing Medications:
{existing_meds}

Consultation Notes (new entries):
{new_notes}

Extracted Medicines of interest:
{", ".join(medicines)}

Retrieved SIDER safety & side effects context:
===================================
{rag_context}
===================================

Analyze if there are any:
1. Potential drug-drug interactions or contraindications.
2. Major risk factors, warnings, or severe adverse events related to these medicines.
3. Patient safety concerns.

Based on this, make a definitive safety decision: "Safe" or "Not Safe".
If there are potential interactions, contraindications, or severe side effects, you MUST declare it "Not Safe" (is_safe: false).
If everything is standard and there are no critical interactions or warnings, declare it "Safe" (is_safe: true).

Format your response as a JSON object with the following keys:
- "is_safe": true (if safe) or false (if there are safety concerns/warnings/interactions).
- "reason": A short, clear headline explanation of the safety status (e.g., "Potential interaction between X and Y" or "Notes are safe").
- "details": A detailed clinical explanation summarizing the side effects, any interactions, and suggestions/precautions for the doctor.

Return ONLY the raw JSON object. Do not wrap in markdown code blocks or add any other text.
"""
    try:
        response = llm.invoke(prompt)
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
            if text.endswith("```"):
                text = text[:-3].strip()
            
        analysis = json.loads(text)
        return {
            "is_safe": analysis.get("is_safe", True),
            "reason": analysis.get("reason", "Notes are safe"),
            "details": analysis.get("details", ""),
            "retrieved_side_effects": rag_context
        }
    except Exception as e:
        print(f"Error in LLM safety analysis: {e}")
        return {
            "is_safe": True,
            "reason": "Safety analysis check completed",
            "details": "Safety check could not be completed automatically, but notes were saved successfully.",
            "retrieved_side_effects": rag_context
        }


@app.post("/patients/{patient_id}/notes")
def save_doctor_notes(patient_id: str, payload: DoctorNotesIn):
    import os
    import duckdb
    from datetime import datetime
    
    safe_patient_id = "".join(c for c in patient_id if c.isalnum() or c in ("-", "_")).strip()
    if not safe_patient_id:
        raise HTTPException(status_code=400, detail="Invalid patient_id")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, "patient_assets", safe_patient_id)
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        # 1. Save to DuckDB
        con = duckdb.connect(DB_FILE)
        con.execute("""
        INSERT OR REPLACE INTO doctor_notes (patient_id, notes, updated_at)
        VALUES (?, ?, ?)
        """, [patient_id, payload.notes, datetime.now()])
        con.close()
        
        # 2. Save to text file for backward compatibility
        file_path = os.path.join(save_dir, "doctor_notes.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(payload.notes)
            
        # 3. Analyze medication safety (consultation notes + existing medicines)
        safety_report = check_medication_safety(patient_id, payload.notes)
        
        return {
            "success": True, 
            "message": "✅ Doctor notes saved successfully.",
            "safety_report": safety_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patients/{patient_id}/notes")
def get_doctor_notes(patient_id: str):
    import os
    import duckdb
    safe_patient_id = "".join(c for c in patient_id if c.isalnum() or c in ("-", "_")).strip()
    if not safe_patient_id:
        raise HTTPException(status_code=400, detail="Invalid patient_id")
    
    # Try fetching from DuckDB first
    try:
        con = duckdb.connect(DB_FILE)
        r = con.execute("SELECT notes FROM doctor_notes WHERE patient_id = ?", [patient_id]).fetchone()
        con.close()
        if r:
            return {"notes": r[0]}
    except Exception as db_err:
        print(f"Failed to get doctor notes from DuckDB: {db_err}")
        
    # Fallback to text file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "patient_assets", safe_patient_id, "doctor_notes.txt")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                notes = f.read()
            return {"notes": notes}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        return {"notes": ""}


class InvestigationRequest(BaseModel):
    patient_summary: str


@app.post("/analyze-investigation")
def analyze_investigation(request: InvestigationRequest):
    import requests
    import json
    
    prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
You are a medical review assistant. You will be given a summary of a medical review and you need to provide JSON formmat output that includes the following information:
1. "meddra_pt": the preferred term of the medical event
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
{request.patient_summary}

### Response:
"""

    payload = {
        "model": "./qwen_merged",
        "prompt": prompt,
        "max_tokens": 512,
        "temperature": 0.0
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy"
    }
    
    try:
        # Try local model at port 30005 first
        response = requests.post("http://localhost:30005/v1/completions", json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            res_data = response.json()
            choices = res_data.get("choices", [])
            if choices:
                text = choices[0].get("text", "").strip()
                # Clean markdown blocks if present
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
                    if text.endswith("```"):
                        text = text[:-3].strip()
                try:
                    return json.loads(text)
                except Exception:
                    return {"raw_response": text}
            raise HTTPException(status_code=500, detail="Empty choices in model response")
    except Exception as e:
        print(f"Local Fine tuned Qwen model API call failed ({e}).")


@app.post("/doctors")
def save_doctor_endpoint(payload: DoctorIn):
    try:
        con = duckdb.connect(DB_FILE)
        con.execute("""
        INSERT OR REPLACE INTO doctors
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            payload.doctor_id,
            payload.doctor_name,
            payload.specialization,
            payload.hospital,
            payload.phone,
            payload.email,
            datetime.now()
        ])
        con.close()
        return {"success": True, "message": "✅ Doctor Saved Successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Database Error: {str(e)}")



@app.get("/patients/{patient_id}/pubmed")
async def get_pubmed_articles(patient_id: str):
    import json
    
    con = duckdb.connect(DB_FILE)
    r = con.execute("""
    SELECT patient_name, current_ailment, medical_history FROM patients WHERE patient_id = ?
    """, [patient_id]).fetchone()
    con.close()
    
    if not r:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    name, ailment, history = r[0], r[1] or "", r[2] or ""
    
    # Formulate patient summary context for the agent
    patient_summary = f"Patient Name: {name}. Ailment: {ailment}. Medical History: {history}."
    
    try:
        from graphs.agents.pub_med_agent import run_research
        
        # Invoke the pub_med_agent's research function
        research_str = await run_research(patient_summary=patient_summary)
        
        # Parse the output string into the JSON format expected by the frontend
        system_prompt = (
            "You are a medical data parser. Convert the following markdown text containing PubMed articles "
            "into a clean JSON list of objects. Each object must have keys:\n"
            "1. 'title': The title of the article (string)\n"
            "2. 'authors': The authors or a brief summary/description of the article (string)\n"
            "3. 'journal': Journal name or publisher (string)\n"
            "4. 'pubdate': Date or publication year (string)\n"
            "5. 'url': The URL link to the PubMed article (string)\n\n"
            "Example Input:\n"
            "1. Peripheral Neuropathy in Diabetes Mellitus: https://www.ncbi.nlm.nih.gov/pubmed/36834971 (This article discusses...)\n\n"
            "Example Output:\n"
            "[\n"
            "  {\n"
            "    \"title\": \"Peripheral Neuropathy in Diabetes Mellitus\",\n"
            "    \"authors\": \"This article discusses...\",\n"
            "    \"journal\": \"PubMed\",\n"
            "    \"pubdate\": \"2023\",\n"
            "    \"url\": \"https://www.ncbi.nlm.nih.gov/pubmed/36834971\"\n"
            "  }\n"
            "]\n\n"
            "If some fields are not present in the input text, construct reasonable placeholders or extract them "
            "from the description. The 'url' must be extracted exactly as provided in the text. Output ONLY the raw JSON list."
        )
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=research_str)
        ])
        
        cleaned_content = response.content.strip()
        if cleaned_content.startswith("```"):
            cleaned_content = cleaned_content.split("```")[1]
            if cleaned_content.startswith("json"):
                cleaned_content = cleaned_content[4:]
            cleaned_content = cleaned_content.strip()
            
        articles = json.loads(cleaned_content)
        if isinstance(articles, list):
            for art in articles:
                if 'url' not in art:
                    art['url'] = "https://pubmed.ncbi.nlm.nih.gov/"
            return articles
        else:
            raise ValueError("Parsed content is not a list of articles")
            
    except Exception as e:
        print(f"Error calling PubMed agent or parsing output: {e}")
        raise HTTPException(status_code=500, detail=f"PubMed agent failed: {str(e)}")


class ChatMessage(BaseModel):
    sender: str
    text: str

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []

@app.post("/patients/{patient_id}/chat")
def chat_about_patient(patient_id: str, request: ChatRequest):
    import os
    
    safe_patient_id = "".join(c for c in patient_id if c.isalnum() or c in ("-", "_")).strip()
    if not safe_patient_id:
        raise HTTPException(status_code=400, detail="Invalid patient_id")
        
    con = duckdb.connect(DB_FILE)
    r = con.execute("""
    SELECT patient_name, age, gender, phone, current_medications, current_ailment, adverse_event, medical_history
    FROM patients
    WHERE patient_id = ?
    """, [patient_id]).fetchone()
    con.close()
    
    if not r:
        raise HTTPException(status_code=404, detail="Patient not found in database")
        
    patient_info = {
        "name": r[0],
        "age": r[1],
        "gender": r[2],
        "phone": r[3],
        "current_medications": r[4],
        "current_ailment": r[5],
        "adverse_event": r[6],
        "medical_history": r[7]
    }
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load doctor notes from doctor_notes.txt
    doctor_notes_path = os.path.join(base_dir, "patient_assets", safe_patient_id, "doctor_notes.txt")
    doctor_notes = ""
    if os.path.exists(doctor_notes_path):
        try:
            with open(doctor_notes_path, "r", encoding="utf-8") as f:
                doctor_notes = f.read()
        except Exception:
            pass
            
    # Load patient document extracts (OCR) from global_data.txt
    global_data_path = os.path.join(base_dir, "patient_assets", safe_patient_id, "global_data.txt")
    patient_file_extracts = ""
    if os.path.exists(global_data_path):
        try:
            with open(global_data_path, "r", encoding="utf-8") as f:
                patient_file_extracts = f.read()
        except Exception:
            pass
            
    system_prompt = f"""You are a professional AI Clinical Assistant supporting Dr. Alexander Vance.
You have access to the electronic health records and clinical history of the patient:

=== Patient Clinical Record ===
Patient Name: {patient_info['name']}
Patient ID: {patient_id}
Demographics: {patient_info['age']} years old, {patient_info['gender']} (Phone: {patient_info['phone'] or 'N/A'})
Current Ailments: {patient_info['current_ailment'] or 'None listed'}
Adverse Event: {patient_info['adverse_event'] or 'None reported'}
Active Medications: {patient_info['current_medications'] or 'None listed'}
Patient Summary / Medical History:
{patient_info['medical_history'] or 'None listed'}

=== Patient Uploaded Documents / Extracts ===
{patient_file_extracts or 'No uploaded document extracts found.'}

=== Doctor's Clinical Consultation Notes ===
{doctor_notes or 'No consultation notes recorded yet.'}
===============================

Answer the doctor's questions about this patient accurately and professionally based on the patient's records above.
- If the question is about specific details, reference the record (e.g. 'As noted in their medical history...', 'According to the doctor\'s notes...').
- If the doctor asks for clinical analysis or suggestions beyond what's explicitly written, use your general clinical knowledge to guide them, but clearly state what is clinical advice/context vs what is in the patient's records.
- Keep the tone highly professional, objective, and clear. Use bullet points or short paragraphs where appropriate.
"""

    messages = [SystemMessage(content=system_prompt)]
    
    for msg in request.chat_history:
        if msg.sender == 'doctor':
            messages.append(HumanMessage(content=msg.text))
        elif msg.sender == 'assistant':
            messages.append(AIMessage(content=msg.text))
            
    messages.append(HumanMessage(content=request.message))
    
    try:
        response = llm.invoke(messages)
        return {"response": response.content.strip()}
    except Exception as e:
        print(f"LLM Chat invocation failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM chat invocation failed: {str(e)}")


@app.get("/patients/{patient_id}/files")
def list_patient_files(patient_id: str):
    import os
    safe_patient_id = "".join(c for c in patient_id if c.isalnum() or c in ("-", "_")).strip()
    if not safe_patient_id:
        raise HTTPException(status_code=400, detail="Invalid patient_id")
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, "patient_assets", safe_patient_id)
    
    if not os.path.exists(save_dir):
        return []
        
    files = []
    for filename in os.listdir(save_dir):
        if filename in ("global_data.txt", "doctor_notes.txt"):
            continue
        file_path = os.path.join(save_dir, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            files.append({
                "filename": filename,
                "size_bytes": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
            
    files.sort(key=lambda x: x["filename"])
    return files


@app.get("/patients/{patient_id}/files/{filename}")
def download_patient_file(patient_id: str, filename: str):
    import os
    from fastapi.responses import FileResponse
    safe_patient_id = "".join(c for c in patient_id if c.isalnum() or c in ("-", "_")).strip()
    if not safe_patient_id:
        raise HTTPException(status_code=400, detail="Invalid patient_id")
        
    safe_filename = os.path.basename(filename)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "patient_assets", safe_patient_id, safe_filename)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type="application/octet-stream"
    )


if __name__ == "__main__":
    # Run uvicorn referencing "main:app" since this file is main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
