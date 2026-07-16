import streamlit as st
import duckdb
from datetime import datetime
import pandas as pd
import uuid
import os # Imported for local file operations

# =====================================================
# PAGE CONFIGURATION & CSS
# =====================================================
st.set_page_config(page_title="Patient Registry", layout="wide")

st.markdown("""
    <style>
    .block-container {
        max-width: 1700px !important;
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE
# =====================================================
DB_FILE = "medical_review.duckdb"

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
    con.close()

init_db()

# =====================================================
# DATABASE OPERATIONS
# =====================================================

def save_patient(patient_id, patient_name, age, gender, phone, current_medications, 
                 current_ailment, adverse_event, medical_history, files):
    try:
        con = duckdb.connect(DB_FILE)
        con.execute("""
        INSERT OR REPLACE INTO patients
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            patient_id, patient_name, age, gender, phone, 
            current_medications, current_ailment, adverse_event, 
            medical_history, datetime.now()
        ])

        if files:
            for idx, file in enumerate(files):
                # Use getvalue() to safely read bytes without exhausting the stream
                blob_data = file.getvalue() 
                con.execute("""
                INSERT INTO attachments
                VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    int(datetime.now().timestamp() * 1000) + idx,
                    patient_id,
                    file.name,
                    "application/octet-stream",
                    blob_data,
                    datetime.now()
                ])
        con.close()
        return True, "✅ Patient Saved Successfully"
    except Exception as e:
        return False, f"❌ {str(e)}"

def save_doctor(doctor_id, doctor_name, specialization, hospital, phone, email):
    try:
        con = duckdb.connect(DB_FILE)
        con.execute("""
        INSERT OR REPLACE INTO doctors
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            doctor_id, doctor_name, specialization, hospital, phone, email, datetime.now()
        ])
        con.close()
        return True, "✅ Doctor Saved Successfully"
    except Exception as e:
        return False, f"❌ {str(e)}"

def get_patient_count_card():
    try:
        con = duckdb.connect(DB_FILE)
        result = con.execute("SELECT COUNT(*) FROM patients").fetchone()
        count = result[0] if result else 0
        con.close()
    except:
        count = 0

    return f"""
    <div style="
        background:#111827;
        border-radius:18px;
        padding:25px;
        border-left:6px solid #10B981;
        box-shadow:0px 8px 24px rgba(0,0,0,0.25);
        margin-bottom: 20px;
    ">
        <div style="color:#9CA3AF; font-size:14px;">
            Registered Patients
        </div>
        <div style="color:white; font-size:40px; font-weight:700; margin-top:10px;">
            {count}
        </div>
    </div>
    """

def get_searched_patients_list(search_query=""):
    try:
        con = duckdb.connect(DB_FILE)
        if search_query.strip():
            term = f"%{search_query.strip()}%"
            rows = con.execute("""
            SELECT patient_id, patient_name
            FROM patients
            WHERE patient_id ILIKE ? OR patient_name ILIKE ?
            ORDER BY created_at DESC
            """, [term, term]).fetchall()
        else:
            rows = con.execute("""
            SELECT patient_id, patient_name
            FROM patients
            ORDER BY created_at DESC
            """).fetchall()
        con.close()

        if not rows:
            return "### 🚫 No Patients Found"

        text = "## Patient Directory\n\n"
        for pid, name in rows:
            text += f"🔹 **{pid}**\n\n{name}\n\n---\n"
        return text
    except:
        return "### ⚠️ Error loading patients"

def load_patients():
    try:
        con = duckdb.connect(DB_FILE)
        df = con.execute("""
        SELECT patient_id, patient_name, age, gender, 
               current_medications, adverse_event, created_at
        FROM patients
        ORDER BY created_at DESC
        """).df()
        con.close()
        return df
    except:
        return pd.DataFrame()

# =====================================================
# UI STATE & CALLBACKS
# =====================================================

if "medical_history" not in st.session_state:
    st.session_state.medical_history = ""

if "current_patient_id" not in st.session_state:
    st.session_state.current_patient_id = f"PAT-{uuid.uuid4().hex[:6].upper()}"

if st.session_state.get("clear_patient_form"):
    st.session_state.medical_history = ""
    st.session_state.clear_patient_form = False

if "doctor_logged_in" not in st.session_state:
    st.session_state.doctor_logged_in = False

def generate_medical_history_callback():
    # --- Save files locally ---
    patient_id = st.session_state.current_patient_id
    
    # Retrieve files from the file_uploader session state using its key
    files = st.session_state.get("uploaded_files", [])
    
    if files:
        # Create directory path: ./Patient Assets/{Patient ID}/
        save_dir = os.path.join("patient_assets", patient_id)
        os.makedirs(save_dir, exist_ok=True)
        
        # Save each file
        for file in files:
            file_path = os.path.join(save_dir, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getvalue())

# =====================================================
# MAIN APP LAYOUT
# =====================================================

st.markdown("# 👤 Medical Registry")

# ==================================
# LEFT SIDEBAR
# ==================================
with st.sidebar:
    
    st.markdown(get_patient_count_card(), unsafe_allow_html=True)
    st.divider()

    # --- LOGIN LOGIC ---
    if not st.session_state.doctor_logged_in:
        st.markdown("### 🔒 Doctor Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary", use_container_width=True):
            if username == "admin" and password == "password":
                st.session_state.doctor_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect username or password.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success("Logged in as Doctor")
        with col2:
            if st.button("Logout"):
                st.session_state.doctor_logged_in = False
                st.rerun()
        
        st.markdown("### 🔍 Find Patient")
        search_query = st.text_input("Search by ID or Name", placeholder="e.g. PAT-123 or John")
        
        with st.container(height=500, border=True):
            st.markdown(get_searched_patients_list(search_query))

# ==================================
# MAIN CONTENT TABS
# ==================================
tab_patient, tab_doctor = st.tabs(["👤 Patient Form", "👨‍⚕️ Doctor Dashboard"])

# ----------------------------------
# PATIENT TAB
# ----------------------------------
with tab_patient:
    
    if "patient_msg" in st.session_state:
        if "✅" in st.session_state.patient_msg:
            st.success(st.session_state.patient_msg)
        else:
            st.error(st.session_state.patient_msg)
        del st.session_state.patient_msg

    col1, col2 = st.columns(2)
    
    with col1:
        patient_id = st.text_input("Patient ID", value=st.session_state.current_patient_id, disabled=True)
        patient_name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, step=1, value=0)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        phone = st.text_input("Phone Number")
        
    with col2:
        current_medications = st.text_area("Current Medications *", height=68, placeholder="Required")
        current_ailment = st.text_area("Current Ailment *", height=68, placeholder="Required")
        
        medical_history = st.text_area("Medical History *", height=140, key="medical_history", placeholder="Required")
        st.button("🧠 Generate Medical History Summary", on_click=generate_medical_history_callback)
        
        adverse_event = st.text_input("Primary Adverse Event")
        attachments = st.file_uploader("Upload Documents", accept_multiple_files=True, key="uploaded_files")

    if st.button("💾 Save Patient", type="primary"):
        if not current_medications.strip() or not current_ailment.strip() or not st.session_state.medical_history.strip():
            st.error("⚠️ Please fill in all mandatory fields: Current Medications, Current Ailment, and Medical History.")
        else:
            success, msg = save_patient(
                patient_id, patient_name, age, gender, phone, 
                current_medications, current_ailment, adverse_event, 
                st.session_state.medical_history, attachments
            )
            
            if success:
                st.session_state.current_patient_id = f"PAT-{uuid.uuid4().hex[:6].upper()}"
                st.session_state.clear_patient_form = True 
                
            st.session_state.patient_msg = msg
            st.rerun()

    st.divider()
    st.markdown("### Patient Database")
    st.dataframe(load_patients(), use_container_width=True, hide_index=True)

# ----------------------------------
# DOCTOR TAB
# ----------------------------------
with tab_doctor:
    
    if not st.session_state.doctor_logged_in:
        st.warning("🔒 Access Denied. Please log in using the sidebar to access the Doctor Dashboard.")
    else:
        st.markdown("### 👨‍⚕️ Register Doctor")
        
        if "doctor_msg" in st.session_state:
            if "✅" in st.session_state.doctor_msg:
                st.success(st.session_state.doctor_msg)
            else:
                st.error(st.session_state.doctor_msg)
            del st.session_state.doctor_msg

        doc_col1, doc_col2 = st.columns(2)
        with doc_col1:
            doctor_id = st.text_input("Doctor ID")
            doctor_name = st.text_input("Doctor Name")
            specialization = st.text_input("Specialization")
        with doc_col2:
            hospital = st.text_input("Hospital")
            doctor_phone = st.text_input("Doctor Phone Number")
            email = st.text_input("Email")

        if st.button("💾 Save Doctor", type="primary"):
            success, msg = save_doctor(doctor_id, doctor_name, specialization, hospital, doctor_phone, email)
            st.session_state.doctor_msg = msg
            st.rerun()