# Project Architecture Diagram

This document describes the high-level architecture of the **LangGraph Guardian** system, detailing the interactions between the React frontend, the FastAPI backend server, database systems, LangGraph nodes, and AI agents.

## Architecture Overview

```mermaid
graph TB
    %% Frontend Components
    subgraph Frontend ["React Frontend (Vite App)"]
        UI["App.jsx UI"]
        PP["Patient Portal (Registration & Vitals)"]
        DP["Doctor Portal (Review, Notes & Safety Checks)"]
        CC["Clinical Chatbot Panel"]
        
        UI --> PP
        UI --> DP
        UI --> CC
    end

    %% Backend Server
    subgraph Backend ["FastAPI Backend (main.py)"]
        API["FastAPI App (Uvicorn Port 8000)"]
        
        subgraph Endpoints ["REST API Endpoints"]
            EPSummary["POST /patient_summary"]
            EPNotes["POST & GET /patients/{id}/notes"]
            EPChat["POST /patients/{id}/chat"]
            EPFiles["GET /patients/{id}/files"]
            EPPubmed["GET /patients/{id}/pubmed"]
        end
        
        API --> Endpoints
    end

    %% Data Storage Layer
    subgraph Databases ["Data Storage Layer"]
        DuckDB[("DuckDB (medical_review.duckdb)")]
        ChromaDB[("Chroma Vector Store (chroma_db)")]
        DiskStorage["Local File System (patient_assets/)"]
        
        subgraph DuckDBTables ["Tables"]
            TabPatients["patients"]
            TabNotes["doctor_notes"]
            TabAttachments["attachments"]
            TabDoctors["doctors"]
        end
        DuckDB --> DuckDBTables
    end

    %% AI & Agentic Workflows
    subgraph AIEngine ["AI & LangGraph Core"]
        LLM["MI300X LLM (llm.py)"]
        
        subgraph Graphs ["LangGraph Orchestration"]
            PSG["Patient Summary Graph (patient_summary_graph.py)"]
            SRG["SIDER RAG Graph (sider_rag_graph.py)"]
            SAG["Symptom Analysis Graph (symptom_analysis_graph.py)"]
        end
        
        subgraph AgentsChains ["Specialized Agents & Chains"]
            PMA["PubMed Agent (pub_med_agent.py)"]
            IC["Multimodal Image Chain (image_chain.py)"]
            PC["PDF Text Chain (pdf_chain.py)"]
        end
    end

    %% Interactions & Data Flows
    PP -- "Register/Update Patient Data" --> EPSummary
    DP -- "Save Notes & Trigger Safety Check" --> EPNotes
    CC -- "Demographic & Notes Queries" --> EPChat
    
    EPSummary --> DuckDB
    EPNotes --> DuckDB
    EPNotes -- "1. Extract Medicines" --> LLM
    EPNotes -- "2. Similarity Search" --> ChromaDB
    EPNotes -- "3. Analyze Safety" --> LLM
    
    EPChat --> DuckDB
    EPChat --> DiskStorage
    EPChat --> LLM
    
    EPPubmed --> PMA
    PMA -- "Scrape articles" --> LLM
    
    %% LangGraph Summarization Pipelines
    EPSummary --> PSG
    PSG --> IC
    PSG --> PC
    PSG --> SRG
    SRG --> ChromaDB
    PSG --> LLM
    
    %% File Storage Links
    IC -- "Read images" --> DiskStorage
    PC -- "Read PDFs" --> DiskStorage
    EPNotes -- "Save txt backup" --> DiskStorage

    %% Styling
    classDef frontend fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#fff;
    classDef backend fill:#111827,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef database fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#fff;
    classDef ai fill:#311042,stroke:#c084fc,stroke-width:2px,color:#fff;
    
    class UI,PP,DP,CC frontend;
    class API,Endpoints,EPSummary,EPNotes,EPChat,EPFiles,EPPubmed backend;
    class DuckDB,ChromaDB,DiskStorage,DuckDBTables,TabPatients,TabNotes,TabAttachments,TabDoctors database;
    class LLM,Graphs,PSG,SRG,SAG,AgentsChains,PMA,IC,PC ai;
```

---

## Component Breakdown

### 1. React Frontend (Vite)
- **App.jsx**: The master dashboard view containing:
  - **Patient Portal**: Renders forms to save names, vitals, active medications, ailments, and upload patient lab reports (PDF/images).
  - **Doctor Portal**: Allows reviewing symptoms, clinical records, and writing **Clinical Consultation Notes**. On saving, it displays a safety dialog highlighting any potential adverse drug-drug interactions or warnings.
  - **Clinical Chatbot**: A chat panel helping doctors query patient information using RAG and chatbot context.

### 2. FastAPI Backend Service (`main.py`)
- Acts as the orchestration and API gateway.
- Receives HTTP POST/GET requests and interfaces directly with the DuckDB database, Chroma DB, and LangGraph modules.

### 3. Data Storage Layer
- **DuckDB (`medical_review.duckdb`)**: Embedded relational database that maintains patient records, uploads, doctor metadata, and clinical consultation notes.
- **Chroma DB (`chroma_db/`)**: Local vector database containing SIDER (Side Effect Resource) drug profiles chunked and indexed. Used for similarity searches to retrieve side-effect profiles during clinical RAG checks.
- **Local File System (`patient_assets/`)**: Disk storage containing uploaded patient files (PDFs, X-rays/images) and text backups (`global_data.txt` and `doctor_notes.txt`) for LLM context grounding.

### 4. AI & LangGraph Core
- **LangGraph Engines**:
  - **Patient Summary Graph**: Runs file ingestion (OCR/Multimodal images/PDFs), queries SIDER RAG for active medications, and generates a concise, context-grounded history summary.
  - **SIDER RAG Graph**: A standard query-retrieve-generate RAG pipeline over Chroma DB drug records.
  - **Symptom Analysis Graph**: Parses clinical logs to isolate matching symptoms and match severity.
- **Agents & Chains**:
  - **PubMed Agent**: A tool-equipped agent that scrapes PubMed dynamically to research medical findings about patient conditions.
  - **Image & PDF Chains**: Lightweight LangChain pipes utilizing multimodal LLM prompts to extract structured text from reports.
