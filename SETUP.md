# AI-Led Medical Review Assistant (Guardian)

This repository contains the complete codebase for **Guardian**, an AI-led Medical Review Assistant designed to support medical reviewers in assessing seriousness, suggesting MedDRA codes, evaluating drug labeling status, and performing causality assessments.

The project is structured as a mono-repository containing:
- **`backend/`**: A FastAPI service exposing LangGraph clinical analysis workflows and a Streamlit dashboard for patient registries.
- **`frontend/`**: A React client built with Vite for the user interface.
- **`fine_tuning/`**: Python pipelines for FAERS XML data parsing, synthetic dataset creation, and model fine-tuning using Unsloth.

---

## Repository Structure

```
.
├── .gitignore                   # Excludes node_modules, huge XML datasets, local databases, and environment configs
├── SETUP.md                     # Root project documentation and setup guide
├── backend/                     # Python backend codebase
│   ├── main.py                  # FastAPI API Server (LangGraph endpoints)
│   ├── stream.py                # Streamlit dashboard for Patient Registry
│   ├── requirements.txt         # Backend Python packages
│   ├── graphs/                  # LangGraph agent definitions
│   └── medical_review.duckdb    # DuckDB state database (git-ignored, auto-initialized)
├── frontend/                    # Vite React web application
│   ├── package.json             # Frontend dependencies
│   ├── vite.config.js           # Vite build configuration
│   ├── src/                     # React application sources
│   └── public/                  # Static assets
└── fine_tuning/                 # Model training and data preprocessing
    ├── unsloth_trainer_new_prog.py # Unsloth training script (PEFT/SFT)
    ├── infer_remote.py          # vLLM inference script
    ├── XML_Parser.py            # Extracts drug and reaction data from FAERS XMLs
    ├── Training_Data_Maker.py   # Synthesizes datasets using structured LLM calls
    └── datasets/                # Source XMLs and synthetic JSON outputs (git-ignored)
```

---

## Getting Started

### 1. Backend Setup

The backend utilizes FastAPI to serve LangGraph agent flows, and Streamlit to serve an admin patient registry view. Both access a local DuckDB instance.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file containing required API credentials (e.g., OpenAI / local LLM base URLs and API keys).
5. Start the FastAPI API Server:
   ```bash
   python main.py  # Runs on http://localhost:8000
   ```
6. Start the Streamlit Patient Registry dashboard:
   ```bash
   streamlit run stream.py  # Runs on http://localhost:8501
   ```

### 2. Frontend Setup

The frontend is a Vite-powered React single page application.

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev  # Runs on http://localhost:5173
   ```
4. To build the production build:
   ```bash
   npm run build
   ```

### 3. Fine-Tuning Setup

The fine-tuning pipeline extracts structured reports from FDA FAERS database XML dumps, passes them through a processing script to generate synthetic medical review cases, and fine-tunes a model like Qwen or Llama using Unsloth.

1. Navigate to the fine-tuning directory:
   ```bash
   cd fine_tuning
   ```
2. Download FDA FAERS XML dataset files and place the ZIP archives under `datasets/faers_xml/` (these are git-ignored to prevent bloating repository size).
3. Run the parser and data synthesizer to compile training data:
   ```bash
   python Training_Data_Maker.py
   ```
   This extracts high-quality serious events and saves synthetic reviews inside `datasets/FAERS_Generated_new/`.
4. Run the Unsloth training script:
   ```bash
   python unsloth_trainer_new_prog.py
   ```
   This will train the model and save the merged output checkpoints to `qwen_merged/` or `fine_models/`.
5. Test inference using vLLM:
   ```bash
   python infer_remote.py
   ```

---

## Git / GitHub Considerations

To ensure the repository remains clean and performant for GitHub, the root `.gitignore` excludes:
- Large database states (`*.duckdb`, `backend/patient_assets/`, `backend/chroma_db/`)
- Raw source dataset files (`fine_tuning/datasets/faers_xml/XML/` and zip archives)
- Intermediate model files and checkpoints (`fine_tuning/models/`, `fine_tuning/fine_models/`, `fine_tuning/qwen_merged/`)
- Frontend dependency directories (`node_modules/`, `dist/`)
