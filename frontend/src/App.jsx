import { useState, useEffect } from 'react';
import './App.css';

// Helper to generate PAT-[HEX6] ID
const generatePatientId = () => {
  const chars = '0123456789ABCDEF';
  let hex = '';
  for (let i = 0; i < 6; i++) {
    hex += chars[Math.floor(Math.random() * chars.length)];
  }
  return `PAT-${hex}`;
};

// Helper to generate deterministic patient ID based on username
const getDeterministicPatientId = (username) => {
  if (!username) return 'PAT-DEFAULT';
  let hash = 0;
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hex = Math.abs(hash).toString(16).toUpperCase().padStart(6, '0').substring(0, 6);
  return `PAT-${hex}`;
};

// API Base URL config for Jupyter reverse-proxy routing
const API_BASE_URL = 'https://notebooks.amd.com/jupyter-hack-team-2730-260616164823-c210d96e/proxy/8000';

// Helper to render user input vs AI generated content separately with highlighting
const renderHighlightedContent = (text) => {
  if (!text) return null;
  if (text.includes("--- USER FILLED ---") && text.includes("--- AI GENERATED ---")) {
    try {
      const parts = text.split("--- USER FILLED ---")[1].split("--- AI GENERATED ---");
      const userInput = parts[0].trim();
      const aiGenerated = parts[1].trim();
      
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px', width: '100%' }}>
          <div style={{
            padding: '8px 12px',
            backgroundColor: 'rgba(59, 130, 246, 0.06)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '8px',
            fontSize: '13px',
            textAlign: 'left'
          }}>
            <span style={{ fontSize: '11px', fontWeight: 'bold', textTransform: 'uppercase', color: '#3B82F6', display: 'block', marginBottom: '4px' }}>
              ✍️ User Provided Details
            </span>
            <span style={{ color: 'var(--text)', whiteSpace: 'pre-wrap' }}>{userInput}</span>
          </div>
          <div style={{
            padding: '8px 12px',
            backgroundColor: 'rgba(16, 185, 129, 0.06)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            borderRadius: '8px',
            fontSize: '13px',
            textAlign: 'left'
          }}>
            <span style={{ fontSize: '11px', fontWeight: 'bold', textTransform: 'uppercase', color: '#10B981', display: 'block', marginBottom: '4px' }}>
              🤖 AI Generated Summary
            </span>
            <span style={{ color: 'var(--text)', whiteSpace: 'pre-wrap' }}>{aiGenerated}</span>
          </div>
        </div>
      );
    } catch (e) {
      // Fallback if split parsing fails
    }
  }
  return <p style={{ margin: '6px 0 0 0', fontSize: '13px', lineHeight: '1.4', color: 'var(--text)', whiteSpace: 'pre-wrap', textAlign: 'left' }}>{text}</p>;
};

// Premium HSL tag configurations
const AILMENT_COLORS = [
  { bg: 'rgba(16, 185, 129, 0.1)', text: '#10B981', border: 'rgba(16, 185, 129, 0.3)' },
  { bg: 'rgba(59, 130, 246, 0.1)', text: '#3B82F6', border: 'rgba(59, 130, 246, 0.3)' },
  { bg: 'rgba(139, 92, 246, 0.1)', text: '#8B5CF6', border: 'rgba(139, 92, 246, 0.3)' },
  { bg: 'rgba(245, 158, 11, 0.1)', text: '#F59E0B', border: 'rgba(245, 158, 11, 0.3)' },
  { bg: 'rgba(239, 68, 68, 0.1)', text: '#EF4444', border: 'rgba(239, 68, 68, 0.3)' },
  { bg: 'rgba(236, 72, 153, 0.1)', text: '#EC4899', border: 'rgba(236, 72, 153, 0.3)' }
];

const getAilmentColor = (index) => AILMENT_COLORS[index % AILMENT_COLORS.length];

export default function GuardianApp() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState('patient');
  const [userRole, setUserRole] = useState('patient');
  const [toast, setToast] = useState(null);

  // Patient Registration Form States
  const [currentPatientId, setCurrentPatientId] = useState(generatePatientId);
  const [patientName, setPatientName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('Male');
  const [phone, setPhone] = useState('');
  const [currentMedications, setCurrentMedications] = useState('');
  const [currentAilment, setCurrentAilment] = useState('');
  const [medicalHistory, setMedicalHistory] = useState('');
  const [adverseEvent, setAdverseEvent] = useState('');
  const [attachments, setAttachments] = useState([]); // Array of { name, size, data }

  // Loaded database data states
  const [dbPatients, setDbPatients] = useState([]);
  const [searchQueryDoc, setSearchQueryDoc] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedPatientForDoctor, setSelectedPatientForDoctor] = useState(null);
  const [doctorNotesText, setDoctorNotesText] = useState('');
  const [isSavingNotes, setIsSavingNotes] = useState(false);
  const [showSafetyModal, setShowSafetyModal] = useState(false);
  const [safetyReport, setSafetyReport] = useState(null);
  const [analyzedData, setAnalyzedData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [investigationData, setInvestigationData] = useState(null);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [investigationError, setInvestigationError] = useState('');

  // Further Resources and Chatbot States
  const [showFurtherResources, setShowFurtherResources] = useState(false);
  const [pubmedArticles, setPubmedArticles] = useState([]);
  const [isLoadingPubmed, setIsLoadingPubmed] = useState(false);
  const [pubmedError, setPubmedError] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatSending, setIsChatSending] = useState(false);

  // Patient Reports/Files Overlay States
  const [showReportsOverlay, setShowReportsOverlay] = useState(false);
  const [patientFiles, setPatientFiles] = useState([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [filesError, setFilesError] = useState('');

  // Form Utility States
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [isSavingPatient, setIsSavingPatient] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [patientMsg, setPatientMsg] = useState('');
  const [hasAutoPopulated, setHasAutoPopulated] = useState(false);

  // Toast notifier
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const showToast = (message) => {
    setToast(message);
  };

  // Trigger database loads when logged in
  useEffect(() => {
    if (isLoggedIn) {
      const fetchData = async () => {
        try {
          // Fetch patients
          const listResponse = await fetch(`${API_BASE_URL}/patients?search_query=${searchQueryDoc}`);
          if (listResponse.ok) {
            const patientsData = await listResponse.json();
            setDbPatients(patientsData);

            // Auto-populate patient demographic details on initial load from database
            if (userRole === 'patient' && !hasAutoPopulated) {
              const myRecord = patientsData.find(p => p.patient_id === getDeterministicPatientId(username));
              if (myRecord) {
                setPatientName(myRecord.patient_name || 'Kimberly Lawrence');
                setAge(myRecord.age !== undefined && myRecord.age !== null ? String(myRecord.age) : '46');
                setGender(myRecord.gender || 'Female');
                setPhone(myRecord.phone || '');
              } else {
                setPatientName('Kimberly Lawrence');
                setAge('46');
                setGender('Female');
                setPhone('');
              }
              // Keep clinical details empty on initial login
              setCurrentMedications('');
              setCurrentAilment('');
              setMedicalHistory('');
              setAdverseEvent('');
              setHasAutoPopulated(true);
            }
          }

          // Count fetch removed
        } catch (err) {
          console.error('Failed to load database content from FastAPI:', err);
        }
      };
      fetchData();
    }
  }, [isLoggedIn, searchQueryDoc, refreshTrigger, userRole, hasAutoPopulated, username]);

  const handleLogin = (e) => {
    e.preventDefault();
    setUserRole(selectedRole);
    setIsLoggedIn(true);
    setHasAutoPopulated(false);
    if (selectedRole === 'patient') {
      setCurrentPatientId(getDeterministicPatientId(username));
      
      // Auto-populate patient details to Kimberly Lawrence by default on login
      setPatientName('Kimberly Lawrence');
      setAge('46');
      setGender('Female');
    }
    showToast(`Signed in successfully as ${selectedRole === 'doctor' ? 'Dr. Alexander' : 'Patient Kimberly'}`);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUsername('');
    setPassword('');
    setValidationError('');
    setPatientMsg('');
    setHasAutoPopulated(false);
    setSelectedPatientForDoctor(null);
    showToast('Signed out of Guardian Registry');
  };

  // LangGraph patient summary call
  const handleGenerateSummary = async () => {
    if (!medicalHistory.trim() && attachments.length === 0) {
      setValidationError('⚠️ Please enter some Medical History text or attach documents to generate summary.');
      showToast('No history text or files provided');
      return;
    }

    setIsGeneratingSummary(true);
    setValidationError('');
    setPatientMsg('');
    
    try {
      const payload = {
        patient_summary: medicalHistory,
        current_ailment: currentAilment,
        patient_id: currentPatientId,
        files: attachments.map(att => ({ name: att.name, data: att.data }))
      };
      
      const response = await fetch(`${API_BASE_URL}/patient_summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Populate returned LangGraph properties back into form textareas
        if (data.patient_summary) {
          setMedicalHistory(data.patient_summary);
        }
        if (data.current_medications) {
          const meds = data.current_medications;
          setCurrentMedications(Array.isArray(meds) ? meds.join('\n') : meds);
        }
        if (data.current_ailment) {
          const ailments = data.current_ailment;
          setCurrentAilment(Array.isArray(ailments) ? ailments.join('\n') : ailments);
        }
        
        showToast('Patient summary generated successfully');
      } else {
        const errText = await response.text();
        setValidationError(`Error generating summary: ${errText}`);
        showToast('Failed to generate summary');
      }
    } catch (error) {
      setValidationError(`API request failed: ${error.message}`);
      showToast('API request failed');
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  // Convert uploaded documents to base64 encoding and add to state
  const handleFileChange = (e) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      files.forEach(file => {
        const reader = new FileReader();
        reader.onloadend = () => {
          setAttachments(prev => [...prev, {
            name: file.name,
            size: (file.size / 1024).toFixed(1) + ' KB',
            data: reader.result // base64 encoded URL data
          }]);
        };
        reader.readAsDataURL(file);
      });
      showToast(`Attached ${files.length} document(s)`);
    }
  };

  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
    showToast('Document removed');
  };

  // Save patient registry to local DuckDB via backend
  const handleSavePatient = async (e) => {
    e.preventDefault();
    setValidationError('');
    setPatientMsg('');

    // Check mandatory fields
    if (!patientName.trim()) {
      setValidationError('⚠️ Please fill in the Patient Name.');
      showToast('Validation failed: Missing Patient Name');
      return;
    }

    setIsSavingPatient(true);
    try {
      const payload = {
        patient_id: currentPatientId,
        patient_name: patientName,
        age: age,
        gender: gender,
        phone: phone,
        current_medications: currentMedications,
        current_ailment: currentAilment,
        adverse_event: adverseEvent,
        medical_history: medicalHistory,
        files: attachments.map(att => ({ name: att.name, data: att.data }))
      };

      const response = await fetch(`${API_BASE_URL}/patients`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        setPatientMsg(data.message || '✅ Patient Saved Successfully');
        showToast('Patient record saved to database');
        
        // Keep demographics, only clear clinical details and attachments once saved
        setCurrentMedications('');
        setCurrentAilment('');
        setMedicalHistory('');
        setAdverseEvent('');
        setAttachments([]);

        // Reload data in background
        setRefreshTrigger(prev => prev + 1);
      } else {
        const errText = await response.text();
        setValidationError(`Database save failed: ${errText}`);
        showToast('Database Error');
      }
    } catch (err) {
      setValidationError(`Failed to connect to local DuckDB server: ${err.message}`);
      showToast('Server connection failed');
    } finally {
      setIsSavingPatient(false);
    }
  };



  // Fetch doctor notes when selected patient changes
  useEffect(() => {
    if (selectedPatientForDoctor) {
      const fetchNotes = async () => {
        try {
          const res = await fetch(`${API_BASE_URL}/patients/${selectedPatientForDoctor.patient_id}/notes`);
          if (res.ok) {
            const data = await res.json();
            setDoctorNotesText(data.notes || '');
          }
        } catch (err) {
          console.error("Failed to load doctor notes:", err);
        }
      };
      fetchNotes();
    } else {
      setTimeout(() => {
        setDoctorNotesText('');
      }, 0);
    }
  }, [selectedPatientForDoctor]);

  const handleSaveNotes = async () => {
    if (!selectedPatientForDoctor) return;
    setIsSavingNotes(true);
    try {
      const res = await fetch(`${API_BASE_URL}/patients/${selectedPatientForDoctor.patient_id}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ notes: doctorNotesText })
      });
      if (res.ok) {
        const data = await res.json();
        showToast('✅ Doctor notes saved successfully');
        if (data.safety_report) {
          setSafetyReport(data.safety_report);
          setShowSafetyModal(true);
        }
      } else {
        showToast('❌ Failed to save notes');
      }
    } catch (err) {
      console.error("Failed to save doctor notes:", err);
      showToast('❌ Server connection error');
    } finally {
      setIsSavingNotes(false);
    }
  };

  const renderLoadingState = (message) => (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '36px', gap: '12px' }}>
      <div style={{
        width: '32px',
        height: '32px',
        border: '3px solid rgba(16, 185, 129, 0.15)',
        borderTopColor: '#10B981',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }} />
      <span className="pulsing-text" style={{ fontSize: '13px', color: 'var(--text)', fontWeight: '600' }}>
        {message}
      </span>
    </div>
  );

  // Run symptom and ailment analysis when selected patient changes
  useEffect(() => {
    if (selectedPatientForDoctor) {
      const runAnalysis = async () => {
        setIsAnalyzing(true);
        setAnalysisError('');
        setAnalyzedData(null);
        try {
          const res = await fetch(`${API_BASE_URL}/analyze-symptoms`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              patient_summary: selectedPatientForDoctor.medical_history || '',
              patient_id: selectedPatientForDoctor.patient_id,
              files: []
            })
          });
          if (res.ok) {
            const data = await res.json();
            setAnalyzedData(data);
          } else {
            const errText = await res.text();
            setAnalysisError(`Failed to analyze symptoms: ${errText}`);
          }
        } catch (err) {
          console.error("Error analyzing symptoms:", err);
          setAnalysisError("Network or server error running symptom analysis");
        } finally {
          setIsAnalyzing(false);
        }
      };
      runAnalysis();
    } else {
      setTimeout(() => {
        setAnalyzedData(null);
        setIsAnalyzing(false);
        setAnalysisError('');
      }, 0);
    }
  }, [selectedPatientForDoctor]);

  // Run medical review investigation when selected patient changes
  useEffect(() => {
    if (selectedPatientForDoctor) {
      const runInvestigation = async () => {
        setIsInvestigating(true);
        setInvestigationError('');
        setInvestigationData(null);
        try {
          const res = await fetch(`${API_BASE_URL}/analyze-investigation`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              patient_summary: selectedPatientForDoctor.medical_history || ''
            })
          });
          if (res.ok) {
            const data = await res.json();
            setInvestigationData(data);
          } else {
            const errText = await res.text();
            setInvestigationError(`Failed to run investigation: ${errText}`);
          }
        } catch (err) {
          console.error("Error running investigation:", err);
          setInvestigationError("Network or server error running investigation");
        } finally {
          setIsInvestigating(false);
        }
      };
      runInvestigation();
    } else {
      setTimeout(() => {
        setInvestigationData(null);
        setIsInvestigating(false);
        setInvestigationError('');
      }, 0);
    }
  }, [selectedPatientForDoctor]);

  // Reset Further Resources states and overlay when patient changes
  useEffect(() => {
    setTimeout(() => {
      setShowFurtherResources(false);
      setPubmedArticles([]);
      setPubmedError('');
      setChatHistory([]);
      setChatInput('');
      setIsChatSending(false);
      setShowReportsOverlay(false);
      setPatientFiles([]);
      setFilesError('');
    }, 0);
  }, [selectedPatientForDoctor]);

  // Fetch PubMed articles when showFurtherResources becomes true
  useEffect(() => {
    if (selectedPatientForDoctor && showFurtherResources) {
      const fetchPubmed = async () => {
        setIsLoadingPubmed(true);
        setPubmedError('');
        setPubmedArticles([]);
        try {
          const res = await fetch(`${API_BASE_URL}/patients/${selectedPatientForDoctor.patient_id}/pubmed`);
          if (res.ok) {
            const data = await res.json();
            setPubmedArticles(data);
          } else {
            const errText = await res.text();
            setPubmedError(`Failed to load research articles: ${errText}`);
          }
        } catch (err) {
          console.error("Error loading PubMed articles:", err);
          setPubmedError("Server connection error loading research articles");
        } finally {
          setIsLoadingPubmed(false);
        }
      };
      fetchPubmed();
    }
  }, [selectedPatientForDoctor, showFurtherResources]);

  // Fetch patient files when showReportsOverlay becomes true
  useEffect(() => {
    if (selectedPatientForDoctor && showReportsOverlay) {
      const fetchFiles = async () => {
        setIsLoadingFiles(true);
        setFilesError('');
        setPatientFiles([]);
        try {
          const res = await fetch(`${API_BASE_URL}/patients/${selectedPatientForDoctor.patient_id}/files`);
          if (res.ok) {
            const data = await res.json();
            setPatientFiles(data);
          } else {
            const errText = await res.text();
            setFilesError(`Failed to load patient reports: ${errText}`);
          }
        } catch (err) {
          console.error("Error loading patient reports:", err);
          setFilesError("Server connection error loading patient reports");
        } finally {
          setIsLoadingFiles(false);
        }
      };
      fetchFiles();
    }
  }, [selectedPatientForDoctor, showReportsOverlay]);

  const handleSendChatMessage = async (e) => {
    if (e) e.preventDefault();
    if (!chatInput.trim() || isChatSending || !selectedPatientForDoctor) return;
    
    const userMsgText = chatInput.trim();
    setChatInput('');
    
    const newHistory = [...chatHistory, { sender: 'doctor', text: userMsgText }];
    setChatHistory(newHistory);
    setIsChatSending(true);
    
    try {
      const res = await fetch(`${API_BASE_URL}/patients/${selectedPatientForDoctor.patient_id}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMsgText,
          chat_history: newHistory.slice(0, -1)
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setChatHistory(prev => [...prev, { sender: 'assistant', text: data.response }]);
      } else {
        const errText = await res.text();
        setChatHistory(prev => [...prev, { sender: 'assistant', text: `⚠️ Error from assistant: ${errText}` }]);
      }
    } catch (err) {
      console.error("Error sending message to clinical chatbot:", err);
      setChatHistory(prev => [...prev, { sender: 'assistant', text: "⚠️ Network or server error connecting to the clinical assistant." }]);
    } finally {
      setIsChatSending(false);
    }
  };



  const myConsultations = dbPatients.filter(p => p.patient_id === currentPatientId);

  const latestConsultation = myConsultations[0];
  const activeMeds = latestConsultation && latestConsultation.current_medications
    ? latestConsultation.current_medications.split(/[\n;]+/).map(med => {
        const parts = med.split(/[-:]/);
        const name = parts[0].trim();
        const instructions = parts[1] ? parts[1].trim() : 'Take as directed by physician.';
        return { name, instructions };
      }).filter(item => item.name.length > 0)
    : [];

  return (
    <div className="app-page-wrapper" style={styles.page}>
      {/* Header Band */}
      <header style={styles.header}>
        <div style={styles.logoContainer}>
          <span style={styles.logoIcon}>⛨</span>
          <span style={styles.logoText}>Guardian</span>
        </div>
        
        {isLoggedIn ? (
          <div className="user-profile-widget">
            <span className={`user-avatar-circle ${userRole === 'doctor' ? 'doctor-avatar-bg' : 'patient-avatar-bg'}`}>
              {userRole === 'doctor' ? 'DR' : 'PT'}
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
              <span style={{ fontWeight: '600' }}>
                {userRole === 'doctor' ? 'Dr. Alexander Vance' : 'Kimberly Lawrence'}
              </span>
              <span className="logout-link" onClick={handleLogout}>Log Out</span>
            </div>
          </div>
        ) : (
          /* Login Form with Role Selection */
          <form onSubmit={handleLogin} style={styles.loginForm}>
            <select
              className="role-select-header"
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              title="Select portal role"
            >
              <option value="patient">Patient Portal</option>
              <option value="doctor">Doctor Portal</option>
            </select>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              required
            />
            <button type="submit" style={styles.button}>
              Login
            </button>
          </form>
        )}
      </header>

      {/* Main Content Area */}
      {!isLoggedIn ? (
        <main style={styles.main} className="fade-in-up">
          <h1 style={styles.welcomeText}>Welcome to Guardian Registry</h1>
          <p style={styles.subText}>Securely manage patient profiles and monitor health records.</p>
          
          <div style={{ 
            marginTop: '30px', 
            padding: '20px', 
            background: 'rgba(139, 92, 246, 0.08)', 
            borderRadius: '12px', 
            border: '1px solid rgba(139, 92, 246, 0.25)', 
            maxWidth: '460px',
            textAlign: 'left'
          }}>
            <span style={{ fontWeight: 'bold', color: '#8B5CF6', fontSize: '15px', display: 'block', marginBottom: '8px' }}>
              🛡️ Role-Based Login Options
            </span>
            <p style={{ fontSize: '13px', color: 'var(--text)', margin: '0 0 12px 0', lineHeight: '1.4' }}>
              Choose your role in the header dropdown and click <strong>Login</strong>:
            </p>
            <ul style={{ fontSize: '13px', color: 'var(--text)', paddingLeft: '20px', margin: 0 }}>
              <li style={{ marginBottom: '6px' }}>
                <strong>Patient Portal</strong>: Access personal health vitals, active medications, and register doctor visit details to a local DuckDB.
              </li>
              <li>
                <strong>Doctor Portal</strong>: Access the clinical workstation, search patients from database, and manage appointments.
              </li>
            </ul>
          </div>
        </main>
      ) : userRole === 'doctor' ? (
        /* Doctor Portal Dashboard (connected to DuckDB) - single card layout */
        <main className="portal-container fade-in-up">
          {selectedPatientForDoctor ? (
            /* Patient Detail View / Clinical Workstation */
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
              {/* Premium header row with back button and patient profile summary */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', paddingBottom: '12px', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  {!showFurtherResources ? (
                    <>
                      <button 
                        onClick={() => setSelectedPatientForDoctor(null)}
                        style={{ 
                          padding: '8px 16px', 
                          fontSize: '14px', 
                          background: 'rgba(16, 185, 129, 0.1)', 
                          color: '#10B981', 
                          border: '1px solid rgba(16, 185, 129, 0.3)', 
                          borderRadius: '8px', 
                          cursor: 'pointer', 
                          fontWeight: 'bold',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          transition: 'all 0.2s'
                        }}
                        onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(16, 185, 129, 0.2)'; }}
                        onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(16, 185, 129, 0.1)'; }}
                      >
                        ← Back to Registry
                      </button>
                      <button 
                        onClick={() => setShowFurtherResources(true)}
                        style={{ 
                          padding: '8px 16px', 
                          fontSize: '14px', 
                          background: 'rgba(59, 130, 246, 0.1)', 
                          color: '#3B82F6', 
                          border: '1px solid rgba(59, 130, 246, 0.3)', 
                          borderRadius: '8px', 
                          cursor: 'pointer', 
                          fontWeight: 'bold',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          transition: 'all 0.2s'
                        }}
                        onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(59, 130, 246, 0.2)'; }}
                        onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(59, 130, 246, 0.1)'; }}
                      >
                        📚 Further Resources
                      </button>
                    </>
                  ) : (
                    <button 
                      onClick={() => setShowFurtherResources(false)}
                      style={{ 
                        padding: '8px 16px', 
                        fontSize: '14px', 
                        background: 'rgba(16, 185, 129, 0.1)', 
                        color: '#10B981', 
                        border: '1px solid rgba(16, 185, 129, 0.3)', 
                        borderRadius: '8px', 
                        cursor: 'pointer', 
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.2s'
                      }}
                      onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(16, 185, 129, 0.2)'; }}
                      onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(16, 185, 129, 0.1)'; }}
                    >
                      ← Back to Workstation
                    </button>
                  )}

                  <button 
                    onClick={() => setShowReportsOverlay(true)}
                    style={{ 
                      padding: '8px 16px', 
                      fontSize: '14px', 
                      background: 'rgba(139, 92, 246, 0.1)', 
                      color: '#8B5CF6', 
                      border: '1px solid rgba(139, 92, 246, 0.3)', 
                      borderRadius: '8px', 
                      cursor: 'pointer', 
                      fontWeight: 'bold',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(139, 92, 246, 0.2)'; }}
                    onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(139, 92, 246, 0.1)'; }}
                  >
                    📁 Patient Reports
                  </button>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="item-avatar-initials" style={{ width: '42px', height: '42px', fontSize: '18px', color: '#10B981', borderColor: 'rgba(16, 185, 129, 0.2)' }}>
                      {selectedPatientForDoctor.patient_name ? selectedPatientForDoctor.patient_name.charAt(0).toUpperCase() : 'PT'}
                    </span>
                    <div>
                      <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '800', color: 'var(--text-h)' }}>
                        {selectedPatientForDoctor.patient_name || 'Anonymous'}
                      </h2>
                      <span style={{ fontSize: '12px', color: 'var(--text)' }}>ID: {selectedPatientForDoctor.patient_id}</span>
                    </div>
                  </div>
                </div>
                <span style={{ fontSize: '14px', color: '#10B981', background: 'rgba(16, 185, 129, 0.1)', padding: '6px 12px', borderRadius: '6px', fontWeight: '700' }}>
                  {selectedPatientForDoctor.gender}, {selectedPatientForDoctor.age} yrs
                </span>
              </div>

              {/* Split Workspace Layout */}
              {!showFurtherResources ? (
                <div className="portal-grid" style={{ flex: 1, minHeight: 0, height: '100%', gap: '16px' }}>
                
                {/* Left Column - Scrollable cards */}
                <div style={{ flex: 1.2, display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '8px', minHeight: 0 }}>
                  
                  {/* Card 1: Patient Summary */}
                  <div className="dashboard-card" style={{ marginBottom: 0, padding: '12px' }}>
                    <h3 style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      👤 Patient Profile Summary
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '14px', color: 'var(--text)' }}>
                      <div><strong>Full Name:</strong> {selectedPatientForDoctor.patient_name || 'N/A'}</div>
                      <div><strong>Patient ID:</strong> {selectedPatientForDoctor.patient_id}</div>
                      <div><strong>Age / Gender:</strong> {selectedPatientForDoctor.age} yrs / {selectedPatientForDoctor.gender}</div>
                      <div><strong>Phone Number:</strong> {selectedPatientForDoctor.phone || 'N/A'}</div>
                      <div style={{ gridColumn: 'span 2' }}>
                        <strong>Admission Date:</strong> {selectedPatientForDoctor.created_at ? new Date(selectedPatientForDoctor.created_at).toLocaleString() : 'N/A'}
                      </div>
                      {selectedPatientForDoctor.current_ailment && (
                        <div style={{ gridColumn: 'span 2', marginTop: '6px', borderTop: '1px dashed var(--border)', paddingTop: '10px' }}>
                          <strong>Current Ailment:</strong>
                          {renderHighlightedContent(selectedPatientForDoctor.current_ailment)}
                        </div>
                      )}
                      {selectedPatientForDoctor.medical_history && (
                        <div style={{ gridColumn: 'span 2', marginTop: '6px', borderTop: '1px dashed var(--border)', paddingTop: '10px' }}>
                          <strong>Medical History Summary:</strong>
                          {renderHighlightedContent(selectedPatientForDoctor.medical_history)}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Card 2: Decoded Ailments */}
                  <div className="dashboard-card" style={{ marginBottom: 0, padding: '12px' }}>
                    <h3 style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      🔍 Decoded Ailments
                    </h3>
                    {isAnalyzing ? (
                      renderLoadingState("Running LLM ailment extraction...")
                    ) : analysisError ? (
                      <p style={{ margin: 0, fontSize: '13px', color: '#EF4444', fontWeight: '600' }}>{analysisError}</p>
                    ) : !analyzedData || !analyzedData.list_of_diseases || analyzedData.list_of_diseases.length === 0 ? (
                      <p style={{ margin: 0, fontSize: '13px', color: 'var(--text)', fontStyle: 'italic' }}>No ailments decoded for this patient summary.</p>
                    ) : (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {analyzedData.list_of_diseases.map((ailment, idx) => {
                          const colors = getAilmentColor(idx);
                          return (
                            <span 
                              key={idx}
                              style={{
                                backgroundColor: colors.bg,
                                color: colors.text,
                                border: `1px solid ${colors.border}`,
                                padding: '6px 12px',
                                borderRadius: '20px',
                                fontSize: '13px',
                                fontWeight: '600',
                                textTransform: 'capitalize'
                              }}
                            >
                              {ailment}
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Card 3: Symptoms Matched */}
                  <div className="dashboard-card" style={{ marginBottom: 0, padding: '12px' }}>
                    <h3 style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      📋 Symptoms Matched against Ailments
                    </h3>
                    {isAnalyzing ? (
                      renderLoadingState("Evaluating symptom match percentages...")
                    ) : analysisError ? (
                      <p style={{ margin: 0, fontSize: '13px', color: '#EF4444', fontWeight: '600' }}>{analysisError}</p>
                    ) : !analyzedData || !analyzedData.list_of_diseases || analyzedData.list_of_diseases.length === 0 ? (
                      <p style={{ margin: 0, fontSize: '13px', color: 'var(--text)', fontStyle: 'italic' }}>No ailments decoded to run matching diagnostics.</p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {analyzedData.list_of_diseases.map((disease, idx) => {
                          const symptomsList = analyzedData.symptoms && analyzedData.symptoms[disease] 
                            ? (Array.isArray(analyzedData.symptoms[disease]) ? analyzedData.symptoms[disease].join(', ') : analyzedData.symptoms[disease]) 
                            : 'Typical symptoms signs.';
                          
                          const matchPct = analyzedData.symptom_match && typeof analyzedData.symptom_match[disease] === 'number'
                            ? Math.round(analyzedData.symptom_match[disease])
                            : 0;
                          
                          return (
                            <div key={idx} style={{ padding: '12px 14px', borderRadius: '10px', backgroundColor: 'var(--code-bg)', border: '1px solid var(--border)' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                <span style={{ fontWeight: '700', fontSize: '14px', color: 'var(--text-h)' }}>{disease}</span>
                                <span style={{ fontWeight: '700', fontSize: '12px', color: '#10B981' }}>{matchPct}% Match</span>
                              </div>
                              <p style={{ fontStyle: 'italic', color: '#9CA3AF', margin: '4px 0 8px 0', fontSize: '13px', fontFamily: 'Georgia, serif' }}>
                                {symptomsList}
                              </p>
                              <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                                <div style={{ height: '100%', background: 'linear-gradient(90deg, #10B981, #3B82F6)', width: `${matchPct}%`, borderRadius: '3px' }} />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Card 4: Doctor's Notes */}
                  <div className="dashboard-card" style={{ marginBottom: 0, padding: '12px' }}>
                    <h3 style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      ✍️ Clinical Consultation Notes
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <textarea
                        value={doctorNotesText}
                        onChange={(e) => setDoctorNotesText(e.target.value)}
                        placeholder="Add clinical observation, diagnostics, or special notes for this patient..."
                        className="form-field-input form-field-textarea"
                        style={{ minHeight: '95px', fontFamily: 'inherit', resize: 'vertical' }}
                      />
                      <button 
                        onClick={handleSaveNotes}
                        disabled={isSavingNotes}
                        className="portal-btn doctor-btn"
                        style={{ width: 'fit-content', padding: '10px 24px', alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}
                      >
                        {isSavingNotes ? 'Saving...' : '💾 Save Notes'}
                      </button>
                    </div>
                  </div>

                </div>

                {/* Right Column - Scrollable cards */}
                <div style={{ flex: 0.8, display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '8px', minHeight: 0 }}>
                  
                  {/* Card 1: Current Medications */}
                  <div className="dashboard-card" style={{ marginBottom: 0, padding: '12px' }}>
                    <h3 style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      💊 Current Medications
                    </h3>
                    {(() => {
                      const selectedMeds = selectedPatientForDoctor.current_medications
                        ? selectedPatientForDoctor.current_medications.split(/[\n,;]+/).map(med => med.trim()).filter(Boolean)
                        : [];
                      return selectedMeds.length === 0 ? (
                        <p style={{ margin: 0, fontSize: '13px', color: 'var(--text)', fontStyle: 'italic' }}>No active medications registered.</p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {selectedMeds.map((med, idx) => (
                            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 12px', borderRadius: '8px', backgroundColor: 'var(--code-bg)', border: '1px solid var(--border)' }}>
                              <span style={{ color: '#8B5CF6', fontSize: '14px' }}>💊</span>
                              <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-h)' }}>{med}</span>
                            </div>
                          ))}
                        </div>
                      );
                    })()}
                  </div>

                  {/* Card 2: LLM Medical Review Investigation */}
                  <div className="dashboard-card" style={{ marginBottom: 0, padding: '12px' }}>
                    <h3 style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      🔎 LLM Medical Review Investigation
                    </h3>
                    {isInvestigating ? (
                      renderLoadingState("Running Medical Review LLM...")
                    ) : investigationError ? (
                      <p style={{ margin: 0, fontSize: '13px', color: '#EF4444', fontWeight: '600' }}>{investigationError}</p>
                    ) : !investigationData ? (
                      <p style={{ margin: 0, fontSize: '13px', color: 'var(--text)', fontStyle: 'italic' }}>No report generated.</p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '13px' }}>
                        
                        {/* MedDRA PT & SOC */}
                        <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: 'var(--code-bg)', border: '1px solid var(--border)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', marginBottom: '6px' }}>
                            <strong>MedDRA PT:</strong>
                            <span style={{ color: 'var(--text-h)', fontWeight: 'bold' }}>{investigationData.meddra_pt}</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                            <strong>MedDRA SOC:</strong>
                            <span style={{ color: 'var(--text)', fontStyle: 'italic' }}>{investigationData.meddra_soc}</span>
                          </div>
                        </div>

                        {/* Events Grid */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                          <div style={{ padding: '10px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                            <strong style={{ fontSize: '11px', display: 'block', color: 'var(--text)', textTransform: 'uppercase', marginBottom: '4px' }}>Primary Event</strong>
                            <span style={{ color: 'var(--text-h)', fontWeight: '600' }}>{investigationData.primary_event}</span>
                          </div>
                          <div style={{ padding: '10px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                            <strong style={{ fontSize: '11px', display: 'block', color: 'var(--text)', textTransform: 'uppercase', marginBottom: '4px' }}>Secondary Event</strong>
                            <span style={{ color: 'var(--text-h)', fontWeight: '600' }}>{investigationData.secondary_events}</span>
                          </div>
                        </div>

                        {/* Explicit Assessments Panel */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <strong style={{ color: 'var(--text)' }}>Seriousness Assessment:</strong>
                            <span style={{ 
                              padding: '3px 8px', 
                              borderRadius: '4px', 
                              fontWeight: 'bold', 
                              fontSize: '11px',
                              backgroundColor: investigationData.seriousness_assessment === 'Serious' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                              color: investigationData.seriousness_assessment === 'Serious' ? '#EF4444' : '#10B981',
                              border: `1px solid ${investigationData.seriousness_assessment === 'Serious' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)'}`
                            }}>
                              {investigationData.seriousness_assessment}
                            </span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <strong style={{ color: 'var(--text)' }}>Causality Assessment:</strong>
                            <span style={{ 
                              padding: '3px 8px', 
                              borderRadius: '4px', 
                              fontWeight: 'bold', 
                              fontSize: '11px',
                              backgroundColor: 'rgba(245, 158, 11, 0.1)',
                              color: '#F59E0B',
                              border: '1px solid rgba(245, 158, 11, 0.2)'
                            }}>
                              {investigationData.causality_assessment}
                            </span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <strong style={{ color: 'var(--text)' }}>Labeling Status:</strong>
                            <span style={{ 
                              padding: '3px 8px', 
                              borderRadius: '4px', 
                              fontWeight: 'bold', 
                              fontSize: '11px',
                              backgroundColor: 'rgba(139, 92, 246, 0.1)',
                              color: '#8B5CF6',
                              border: '1px solid rgba(139, 92, 246, 0.2)'
                            }}>
                              {investigationData.labeling_status}
                            </span>
                          </div>
                        </div>

                        {/* Confidence Score */}
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '12px' }}>
                            <strong>Review Confidence Score:</strong>
                            <span style={{ fontWeight: 'bold', color: '#3B82F6' }}>{Math.round(parseFloat(investigationData.review_confidence_score) * 100)}%</span>
                          </div>
                          <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', backgroundColor: '#3B82F6', width: `${parseFloat(investigationData.review_confidence_score) * 100}%` }} />
                          </div>
                        </div>

                        {/* Rationales details */}
                        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <div>
                            <strong style={{ fontSize: '11px', display: 'block', color: 'var(--text)' }}>Seriousness Rationale:</strong>
                            <p style={{ margin: '2px 0 0 0', color: 'var(--text-h)', fontSize: '12px', lineHeight: '1.4' }}>{investigationData.seriousness_rationale}</p>
                          </div>
                          <div>
                            <strong style={{ fontSize: '11px', display: 'block', color: 'var(--text)' }}>Causality Rationale:</strong>
                            <p style={{ margin: '2px 0 0 0', color: 'var(--text-h)', fontSize: '12px', lineHeight: '1.4' }}>{investigationData.causality_rationale}</p>
                          </div>
                          <div>
                            <strong style={{ fontSize: '11px', display: 'block', color: 'var(--text)' }}>Labeling Rationale:</strong>
                            <p style={{ margin: '2px 0 0 0', color: 'var(--text-h)', fontSize: '12px', lineHeight: '1.4' }}>{investigationData.labeling_rationale}</p>
                          </div>
                        </div>

                      </div>
                    )}
                  </div>

                  {/* Card 3: Suggested Lab Tests */}
                  <div className="dashboard-card" style={{ marginBottom: 0, padding: '12px' }}>
                    <h3 style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      🧪 Suggested Lab Tests
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {[
                        { name: "Complete Blood Count (CBC)", status: "Recommended" },
                        { name: "Comprehensive Metabolic Panel (CMP)", status: "Recommended" },
                        { name: "Electrocardiogram (ECG / EKG)", status: "Pending Clinical Decision" },
                        { name: "Liver Function Panel (LFT)", status: "Pending Clinical Decision" },
                        { name: "Renal Clearance Panel", status: "Recommended" }
                      ].map((test, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: '8px', backgroundColor: 'var(--code-bg)', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-h)' }}>{test.name}</span>
                          <span style={{ 
                            fontSize: '11px', 
                            padding: '3px 8px', 
                            borderRadius: '4px', 
                            fontWeight: 'bold',
                            backgroundColor: test.status === "Recommended" ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                            color: test.status === "Recommended" ? '#10B981' : '#F59E0B'
                          }}>{test.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              </div>
            ) : (
                /* Split Workspace Layout - Further Resources */
                <div className="portal-grid" style={{ flex: 1, minHeight: 0, height: '100%', gap: '16px' }}>
                  
                  {/* Left Column - PubMed Reference Library */}
                  <div style={{ flex: 1.2, display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '8px', minHeight: 0 }}>
                    <div className="dashboard-card" style={{ marginBottom: 0, padding: '12px', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
                      <h3 style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        📚 PubMed Reference Library
                      </h3>
                      {isLoadingPubmed ? (
                        renderLoadingState("Searching PubMed database for relevant cases...")
                      ) : pubmedError ? (
                        <p style={{ margin: 0, fontSize: '13px', color: '#EF4444', fontWeight: '600' }}>{pubmedError}</p>
                      ) : pubmedArticles.length === 0 ? (
                        <p style={{ margin: 0, fontSize: '13px', color: 'var(--text)', fontStyle: 'italic' }}>No relevant PubMed articles found.</p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', flex: 1 }}>
                          {pubmedArticles.map((art, idx) => (
                            <div key={idx} style={{ padding: '14px', borderRadius: '10px', backgroundColor: 'var(--code-bg)', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                              <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#3B82F6', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                📄 Journal Article
                              </span>
                              <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '700', color: 'var(--text-h)', lineHeight: '1.3' }}>
                                {art.title}
                              </h4>
                              <p style={{ margin: 0, fontSize: '12px', color: 'var(--text)', fontStyle: 'italic' }}>
                                {art.authors}
                              </p>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px', fontSize: '11px', color: '#9CA3AF' }}>
                                <span>{art.journal} • {art.pubdate}</span>
                                <a 
                                  href={art.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer" 
                                  style={{ color: '#10B981', fontWeight: 'bold', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                                >
                                  Read Article ↗
                                </a>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right Column - Clinical Workstation Assistant */}
                  <div style={{ flex: 0.8, display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '8px', minHeight: 0 }}>
                    <div className="dashboard-card" style={{ marginBottom: 0, padding: '12px', display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
                      <h3 style={{ margin: '0 0 14px 0', fontSize: '16px', fontWeight: '700', color: 'var(--text-h)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        💬 AI Clinical Assistant
                      </h3>
                      
                      {/* Chat messages container */}
                      <div 
                        style={{ 
                          flex: 1, 
                          overflowY: 'auto', 
                          marginBottom: '14px', 
                          display: 'flex', 
                          flexDirection: 'column', 
                          gap: '12px', 
                          paddingRight: '4px',
                          minHeight: 0
                        }}
                      >
                        {chatHistory.length === 0 && (
                          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text)', fontSize: '13px', fontStyle: 'italic', margin: 'auto' }}>
                            Ask me any question about patient demographics, active medications, history summary, or consultation notes.
                          </div>
                        )}
                        {chatHistory.map((msg, idx) => (
                          <div 
                            key={idx} 
                            style={{ 
                              display: 'flex', 
                              justifyContent: msg.sender === 'doctor' ? 'flex-end' : 'flex-start',
                              width: '100%' 
                            }}
                          >
                            <div 
                              style={{ 
                                maxWidth: '85%', 
                                padding: '10px 14px', 
                                borderRadius: '12px', 
                                fontSize: '13px', 
                                lineHeight: '1.4',
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                                backgroundColor: msg.sender === 'doctor' ? 'rgba(16, 185, 129, 0.12)' : 'var(--code-bg)',
                                color: msg.sender === 'doctor' ? 'var(--text-h)' : 'var(--text)',
                                border: msg.sender === 'doctor' ? '1px solid rgba(16, 185, 129, 0.25)' : '1px solid var(--border)',
                                borderTopRightRadius: msg.sender === 'doctor' ? '2px' : '12px',
                                borderTopLeftRadius: msg.sender === 'doctor' ? '12px' : '2px'
                              }}
                            >
                              <strong style={{ fontSize: '11px', display: 'block', marginBottom: '4px', color: msg.sender === 'doctor' ? '#10B981' : '#8B5CF6' }}>
                                {msg.sender === 'doctor' ? 'Dr. Vance' : 'Clinical Assistant'}
                              </strong>
                              {msg.text}
                            </div>
                          </div>
                        ))}
                        {isChatSending && (
                          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                            <div style={{ padding: '10px 14px', borderRadius: '12px', backgroundColor: 'var(--code-bg)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{ display: 'flex', gap: '4px' }}>
                                <span style={{ width: '6px', height: '6px', backgroundColor: '#8B5CF6', borderRadius: '50%', display: 'inline-block', animation: 'bounce 1.4s infinite ease-in-out both' }} />
                                <span style={{ width: '6px', height: '6px', backgroundColor: '#8B5CF6', borderRadius: '50%', display: 'inline-block', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.2s' }} />
                                <span style={{ width: '6px', height: '6px', backgroundColor: '#8B5CF6', borderRadius: '50%', display: 'inline-block', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.4s' }} />
                              </div>
                              <span style={{ fontSize: '12px', color: 'var(--text)', fontStyle: 'italic' }}>Assistant is thinking...</span>
                            </div>
                          </div>
                        )}
                      </div>
    
                      {/* Chat input form */}
                      <form onSubmit={handleSendChatMessage} style={{ display: 'flex', gap: '8px', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
                        <input 
                          type="text" 
                          placeholder="Type clinical query or medication checkpoint..." 
                          className="form-field-input"
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          disabled={isChatSending}
                          style={{ flex: 1, padding: '10px 12px', fontSize: '13px' }}
                        />
                        <button 
                          type="submit" 
                          className="portal-btn doctor-btn"
                          disabled={isChatSending || !chatInput.trim()}
                          style={{ width: 'fit-content', padding: '10px 18px', margin: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                        >
                          Send
                        </button>
                      </form>
                    </div>
                  </div>
    
                </div>
              )}

              {/* Patient Reports Overlay Modal */}
              {showReportsOverlay && (
                <div style={{
                  position: 'fixed',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  backgroundColor: 'rgba(0, 0, 0, 0.75)',
                  backdropFilter: 'blur(8px)',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  zIndex: 9999
                }}>
                  <div style={{
                    width: '600px',
                    maxWidth: '90%',
                    backgroundColor: '#111827',
                    border: '1px solid #374151',
                    borderRadius: '12px',
                    padding: '24px',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4)',
                    display: 'flex',
                    flexDirection: 'column',
                    maxHeight: '80%'
                  }}>
                    {/* Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #374151', paddingBottom: '12px', marginBottom: '16px' }}>
                      <h3 style={{ margin: 0, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '18px' }}>
                        📁 Patient Uploaded Reports
                      </h3>
                      <button 
                        onClick={() => setShowReportsOverlay(false)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#ffffff',
                          fontSize: '24px',
                          cursor: 'pointer',
                          padding: '0 4px',
                          lineHeight: 1
                        }}
                      >
                        ×
                      </button>
                    </div>

                    {/* Content */}
                    <div style={{ flex: 1, overflowY: 'auto', marginBottom: '16px' }}>
                      <p style={{ fontSize: '14px', color: '#e5e7eb', marginBottom: '16px' }}>
                        Uploaded files for <strong style={{ color: '#ffffff' }}>{selectedPatientForDoctor.patient_name}</strong> ({selectedPatientForDoctor.patient_id}):
                      </p>

                      {isLoadingFiles ? (
                        <div style={{ padding: '40px 0', textAlign: 'center', color: '#e5e7eb' }}>
                          <div style={{ width: '24px', height: '24px', border: '3px solid rgba(16, 185, 129, 0.15)', borderTopColor: '#10B981', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 12px auto' }}></div>
                          <span>Loading files...</span>
                        </div>
                      ) : filesError ? (
                        <div style={{ padding: '16px', borderRadius: '8px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#EF4444', fontSize: '13px' }}>
                          {filesError}
                        </div>
                      ) : patientFiles.length === 0 ? (
                        <div style={{ padding: '32px', textAlign: 'center', border: '1px dashed #374151', borderRadius: '8px', color: '#9ca3af', fontSize: '13px' }}>
                          No files uploaded for this patient.
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {patientFiles.map(file => (
                            <div 
                              key={file.filename}
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '12px 16px',
                                backgroundColor: '#1f2937',
                                border: '1px solid #374151',
                                borderRadius: '8px',
                                transition: 'all 0.2s'
                              }}
                            >
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxWidth: '70%', alignItems: 'flex-start', textAlign: 'left' }}>
                                <span style={{ fontSize: '13px', fontWeight: '600', color: '#ffffff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', width: '100%', display: 'block' }}>
                                  {file.filename}
                                </span>
                                <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                                  {(file.size_bytes / 1024).toFixed(1)} KB • {new Date(file.modified_time).toLocaleString()}
                                </span>
                              </div>
                              <a 
                                href={`${API_BASE_URL}/patients/${selectedPatientForDoctor.patient_id}/files/${encodeURIComponent(file.filename)}`}
                                download={file.filename}
                                target="_blank"
                                rel="noreferrer"
                                style={{
                                  padding: '6px 12px',
                                  fontSize: '12px',
                                  background: 'rgba(16, 185, 129, 0.1)',
                                  color: '#10B981',
                                  border: '1px solid rgba(16, 185, 129, 0.3)',
                                  borderRadius: '6px',
                                  cursor: 'pointer',
                                  fontWeight: 'bold',
                                  textDecoration: 'none',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '4px',
                                  transition: 'all 0.2s'
                                }}
                                onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(16, 185, 129, 0.2)'; }}
                                onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(16, 185, 129, 0.1)'; }}
                              >
                                📥 Download
                              </a>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Footer */}
                    <div style={{ borderTop: '1px solid #374151', paddingTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
                      <button 
                        onClick={() => setShowReportsOverlay(false)}
                        className="portal-btn doctor-btn"
                        style={{ width: 'fit-content', padding: '8px 16px', margin: 0 }}
                      >
                        Close
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Safety Check Modal */}
              {showSafetyModal && safetyReport && (
                <div style={{
                  position: 'fixed',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  backgroundColor: 'rgba(0, 0, 0, 0.75)',
                  backdropFilter: 'blur(8px)',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  zIndex: 9999
                }}>
                  <div style={{
                    width: '650px',
                    maxWidth: '92%',
                    backgroundColor: '#111827',
                    border: '1px solid ' + (safetyReport.is_safe ? '#10B981' : '#EF4444'),
                    borderRadius: '12px',
                    padding: '24px',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4)',
                    display: 'flex',
                    flexDirection: 'column',
                    maxHeight: '85%',
                    color: '#ffffff'
                  }}>
                    {/* Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #374151', paddingBottom: '12px', marginBottom: '16px' }}>
                      <h3 style={{ margin: 0, color: safetyReport.is_safe ? '#10B981' : '#EF4444', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '20px', fontWeight: 'bold' }}>
                        {safetyReport.is_safe ? '✅ Medication Safety Check: Safe' : '⚠️ Medication Safety Warning: Action Required'}
                      </h3>
                      <button 
                        onClick={() => setShowSafetyModal(false)}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#ffffff',
                          fontSize: '24px',
                          cursor: 'pointer',
                          padding: '0 4px',
                          lineHeight: 1
                        }}
                      >
                        ×
                      </button>
                    </div>

                    {/* Content */}
                    <div style={{ overflowY: 'auto', flex: 1, paddingRight: '4px', marginBottom: '20px', textAlign: 'left' }}>
                      <div style={{ backgroundColor: safetyReport.is_safe ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid ' + (safetyReport.is_safe ? '#10B981' : '#EF4444'), padding: '12px 16px', borderRadius: '4px', marginBottom: '16px' }}>
                        <h4 style={{ margin: '0 0 6px 0', fontSize: '15px', fontWeight: '700', color: safetyReport.is_safe ? '#10B981' : '#EF4444' }}>
                          Reason: {safetyReport.reason}
                        </h4>
                      </div>

                      <div style={{ marginBottom: '16px' }}>
                        <h4 style={{ margin: '0 0 8px 0', fontSize: '15px', fontWeight: '700', color: '#ffffff' }}>Analysis Details</h4>
                        <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.6, color: '#D1D5DB', whiteSpace: 'pre-line' }}>
                          {safetyReport.details}
                        </p>
                      </div>

                      {safetyReport.retrieved_side_effects && (
                        <div>
                          <h4 style={{ margin: '0 0 8px 0', fontSize: '15px', fontWeight: '700', color: '#ffffff' }}>Retrieved SIDER Database Context (RAG)</h4>
                          <div style={{ backgroundColor: '#1F2937', padding: '12px', borderRadius: '8px', border: '1px solid #374151', fontSize: '13px', color: '#9CA3AF', maxHeight: '180px', overflowY: 'auto', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                            {safetyReport.retrieved_side_effects}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid #374151', paddingTop: '16px' }}>
                      <button 
                        onClick={() => setShowSafetyModal(false)}
                        className="portal-btn"
                        style={{
                          backgroundColor: safetyReport.is_safe ? '#10B981' : '#EF4444',
                          color: '#ffffff',
                          border: 'none',
                          padding: '10px 24px',
                          borderRadius: '6px',
                          fontWeight: '600',
                          cursor: 'pointer'
                        }}
                      >
                        Acknowledge & Close
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Patient Database Listings */
            <div className="dashboard-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, marginBottom: 0 }}>
              <div className="card-title-row">
                <h2>📋 Active Database Patient Registry</h2>
                <button 
                  style={{ padding: '6px 12px', fontSize: '12px', background: '#10B981', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
                  onClick={() => setRefreshTrigger(prev => prev + 1)}
                >
                  🔄 Refresh Data
                </button>
              </div>

              {/* Filter and search bar */}
              <div style={{ marginBottom: '18px', display: 'flex', gap: '10px' }}>
                <input 
                  type="text" 
                  placeholder="Search by ID, Name, or Condition..." 
                  className="form-field-input" 
                  value={searchQueryDoc}
                  onChange={(e) => setSearchQueryDoc(e.target.value)}
                  style={{ flex: 1, padding: '10px 14px' }}
                />
              </div>
              
              {dbPatients.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '36px', color: 'var(--text)', border: '1px dashed var(--border)', borderRadius: '12px', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <p style={{ fontSize: '15px', fontWeight: '600' }}>No registered patient records found in medical_review.duckdb.</p>
                </div>
              ) : (
                <div className="clinical-list" style={{ flex: 1, overflowY: 'auto', paddingRight: '8px' }}>
                  {dbPatients.map(patient => (
                    <div 
                      key={patient.patient_id} 
                      className="list-item" 
                      onClick={() => setSelectedPatientForDoctor(patient)}
                      style={{ flexDirection: 'column', alignItems: 'stretch', gap: '8px', cursor: 'pointer' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span className="item-avatar-initials" style={{ color: '#10B981', borderColor: 'rgba(16, 185, 129, 0.2)' }}>
                            {patient.patient_name ? patient.patient_name.charAt(0).toUpperCase() : 'PT'}
                          </span>
                          <div>
                            <span style={{ fontWeight: 'bold', color: 'var(--text-h)', fontSize: '15px' }}>{patient.patient_name || 'Anonymous'}</span>
                            <span style={{ fontSize: '12px', color: 'var(--text)', marginLeft: '8px' }}>({patient.patient_id})</span>
                          </div>
                        </div>
                        <span style={{ fontSize: '12px', color: '#10B981', background: 'rgba(16, 185, 129, 0.1)', padding: '3px 8px', borderRadius: '4px', fontWeight: '700' }}>
                          {patient.gender}, {patient.age} yrs
                        </span>
                      </div>
                      
                      <div style={{ fontSize: '13px', color: 'var(--text)', borderTop: '1px dashed var(--border)', paddingTop: '8px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        <div>
                          <strong>Current Ailment:</strong> {patient.current_ailment || 'Not specified'}
                        </div>
                        <div>
                          <strong>Adverse Event:</strong> {patient.adverse_event || 'None'}
                        </div>
                      </div>

                      <div style={{ fontSize: '12px', color: 'var(--text)', fontStyle: 'italic', background: 'var(--code-bg)', padding: '8px', borderRadius: '6px' }}>
                        <strong>Medications:</strong> {patient.current_medications || 'None'}
                      </div>

                      {patient.medical_history && (
                        <div style={{ fontSize: '12px', color: 'var(--text)' }}>
                          <strong>History Summary:</strong> {patient.medical_history}
                        </div>
                      )}

                      <div style={{ fontSize: '11px', color: 'var(--text)', textAlign: 'right' }}>
                        Admitted: {patient.created_at ? new Date(patient.created_at).toLocaleString() : 'N/A'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </main>
      ) : (
        /* Patient Portal Dashboard (Contains Doctor Visit Registry Form) */
        <main className="portal-container fade-in-up">

          <div className="portal-grid">
            {/* Left Column - Vitals & Doctor Visit Form */}
            <div className="portal-column-left">

              {/* Register Doctor Visit Form */}
              <div className="dashboard-card">
                <div className="card-title-row">
                  <h2>📋 Register Doctor Visit Consultation</h2>
                  <span style={{ fontSize: '12px', color: 'var(--text)' }}>* Mandatory Fields</span>
                </div>

                {/* Validation Banner or Success Msg */}
                {validationError && (
                  <div className="validation-warning-banner">
                    <span>⚠️</span>
                    <span>{validationError}</span>
                  </div>
                )}
                
                {patientMsg && (
                  <div className="validation-warning-banner" style={{ backgroundColor: 'rgba(16, 185, 129, 0.08)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#059669' }}>
                    <span>💾</span>
                    <span>{patientMsg}</span>
                  </div>
                )}

                <form onSubmit={handleSavePatient} style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                  <div style={{ flex: 1, overflowY: 'auto', paddingRight: '8px', marginBottom: '16px' }}>
                  <div className="form-columns-grid">
                    {/* Column 1 - Demographics */}
                    <div>
                      <div className="form-field-group">
                        <label htmlFor="patientId">Patient ID</label>
                        <input 
                          type="text" 
                          id="patientId" 
                          className="form-field-input" 
                          value={currentPatientId} 
                          disabled 
                        />
                      </div>

                      <div className="form-field-group">
                        <label htmlFor="patientName">Patient Name</label>
                        <input 
                          type="text" 
                          id="patientName" 
                          className="form-field-input" 
                          value={patientName} 
                          onChange={(e) => setPatientName(e.target.value)} 
                          placeholder="Enter patient full name"
                        />
                      </div>

                      <div className="form-field-group">
                        <label htmlFor="patientAge">Age</label>
                        <input 
                          type="number" 
                          id="patientAge" 
                          className="form-field-input" 
                          value={age} 
                          onChange={(e) => setAge(e.target.value === '' ? '' : Math.max(0, parseInt(e.target.value) || 0))} 
                          min="0"
                          step="1"
                        />
                      </div>

                      <div className="form-field-group">
                        <label htmlFor="patientGender">Gender</label>
                        <select 
                          id="patientGender" 
                          className="form-field-input" 
                          value={gender} 
                          onChange={(e) => setGender(e.target.value)}
                        >
                          <option value="Male">Male</option>
                          <option value="Female">Female</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>

                      <div className="form-field-group">
                        <label htmlFor="patientPhone">Phone Number</label>
                        <input 
                          type="text" 
                          id="patientPhone" 
                          className="form-field-input" 
                          value={phone} 
                          onChange={(e) => setPhone(e.target.value)} 
                          placeholder="Enter phone number"
                        />
                      </div>
                    </div>

                    {/* Column 2 - Clinical details */}
                    <div>
                      <div className="form-field-group">
                        <div className="field-label-wrapper">
                          <label htmlFor="currentMedications" style={{ marginBottom: 0 }}>Current Medications</label>
                          {isGeneratingSummary && (
                            <span className="field-loading-text">
                              <span className="field-spinner"></span>
                              Analyzing...
                            </span>
                          )}
                        </div>
                        <textarea 
                          id="currentMedications" 
                          className="form-field-input form-field-textarea" 
                          value={currentMedications} 
                          onChange={(e) => setCurrentMedications(e.target.value)} 
                          placeholder="Enter current medications (or auto-generate)"
                        />
                      </div>

                      <div className="form-field-group">
                        <div className="field-label-wrapper">
                          <label htmlFor="currentAilment" style={{ marginBottom: 0 }}>Current Ailment</label>
                          {isGeneratingSummary && (
                            <span className="field-loading-text">
                              <span className="field-spinner"></span>
                              Analyzing...
                            </span>
                          )}
                        </div>
                        <textarea 
                          id="currentAilment" 
                          className="form-field-input form-field-textarea" 
                          value={currentAilment} 
                          onChange={(e) => setCurrentAilment(e.target.value)} 
                          placeholder="Enter current ailment (or auto-generate)"
                        />
                      </div>

                      <div className="form-field-group" style={{ marginBottom: '10px' }}>
                        <div className="field-label-wrapper">
                          <label htmlFor="medicalHistory" style={{ marginBottom: 0 }}>Medical History</label>
                          {isGeneratingSummary && (
                            <span className="field-loading-text">
                              <span className="field-spinner"></span>
                              Analyzing...
                            </span>
                          )}
                        </div>
                        <textarea 
                          id="medicalHistory" 
                          className="form-field-input form-field-textarea" 
                          style={{ minHeight: '120px' }}
                          value={medicalHistory} 
                          onChange={(e) => setMedicalHistory(e.target.value)} 
                          placeholder="Enter medical history (or auto-generate)"
                        />
                      </div>

                      {/* LangGraph Summary Button */}
                      <button 
                        type="button" 
                        className="ai-summary-btn" 
                        onClick={handleGenerateSummary}
                        disabled={isGeneratingSummary}
                      >
                        {isGeneratingSummary ? (
                          <>
                            <span className="spinner-icon"></span>
                            <span>Generating Summary...</span>
                          </>
                        ) : (
                          <>
                            <span>🧠</span>
                            <span>Generate Medical History Summary</span>
                          </>
                        )}
                      </button>

                      <div className="form-field-group">
                        <label htmlFor="adverseEvent">Primary Adverse Event</label>
                        <input 
                          type="text" 
                          id="adverseEvent" 
                          className="form-field-input" 
                          value={adverseEvent} 
                          onChange={(e) => setAdverseEvent(e.target.value)} 
                          placeholder="e.g. Dizziness, nausea"
                        />
                      </div>

                      {/* Document Uploader */}
                      <div className="form-field-group">
                        <label>Upload Documents</label>
                        <div className="file-upload-zone">
                          <span>📁 Drag files here or click to select</span>
                          <span style={{ fontSize: '11px', color: 'var(--text)' }}>Accepts multiple files</span>
                          <input 
                            type="file" 
                            className="file-upload-input" 
                            multiple 
                            onChange={handleFileChange} 
                          />
                        </div>
                        
                        {attachments.length > 0 && (
                          <div className="file-list">
                            {attachments.map((file, i) => (
                              <div key={i} className="file-item">
                                <span>📄 {file.name} ({file.size})</span>
                                <button 
                                  type="button" 
                                  className="file-remove-btn" 
                                  onClick={() => removeAttachment(i)}
                                  title="Remove document"
                                >
                                  &times;
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  </div>
                  {/* Submit Footer */}
                  <div style={{ borderTop: '1px solid var(--border)', paddingTop: '20px', textAlign: 'right' }}>
                    <button type="submit" className="submit-visit-btn" disabled={isSavingPatient}>
                      {isSavingPatient ? (
                        <>
                          <span className="spinner-icon"></span>
                          <span>Saving Patient...</span>
                        </>
                      ) : (
                        <>
                          <span>💾</span>
                          <span>Save Patient</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>

            {/* Right Column - Medications, Appointments, Actions */}
            <div className="portal-column-right">
              {/* My Registered Consultations Log */}
              <div className="dashboard-card">
                <div className="card-title-row">
                  <h2>📋 My Registered Consultations</h2>
                  <span style={{ fontSize: '12px', color: '#8B5CF6', fontWeight: 'bold' }}>
                    {myConsultations.length} Visits
                  </span>
                </div>

                {myConsultations.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text)', border: '1px dashed var(--border)', borderRadius: '12px' }}>
                    <p style={{ fontSize: '13px', margin: 0 }}>No visit history logged under this Patient ID.</p>
                  </div>
                ) : (
                  <div className="clinical-list">
                    {myConsultations.map((consult, idx) => (
                      <div key={idx} className="list-item" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '8px', borderLeft: '4px solid #8B5CF6' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <strong style={{ color: 'var(--text-h)', fontSize: '14px' }}>
                            🩺 {consult.current_ailment}
                          </strong>
                          <span style={{ fontSize: '11px', color: 'var(--text)' }}>
                            {consult.created_at ? new Date(consult.created_at).toLocaleDateString() : 'N/A'}
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text)' }}>
                          <strong>Medications:</strong> {consult.current_medications}
                        </div>
                        {consult.adverse_event && (
                          <div style={{ fontSize: '12px', color: '#EF4444' }}>
                            <strong>Adverse Event:</strong> {consult.adverse_event}
                          </div>
                        )}
                        {consult.medical_history && (
                          <div style={{ fontSize: '11px', color: 'var(--text)', background: 'var(--code-bg)', padding: '6px', borderRadius: '4px', fontStyle: 'italic', marginTop: '4px' }}>
                            {consult.medical_history}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Medications */}
              <div className="dashboard-card">
                <div className="card-title-row">
                  <h2>💊 Active Medications</h2>
                </div>
                
                <div className="clinical-list">
                  {activeMeds.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text)', fontSize: '13px' }}>
                      No active medications saved yet. Fill and save the form to add medications.
                    </div>
                  ) : (
                    activeMeds.map((med, index) => (
                      <div key={index} className="list-item" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 'bold', color: 'var(--text-h)' }}>{med.name}</span>
                          <span style={{ fontSize: '11px', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10B981', padding: '2px 6px', borderRadius: '4px' }}>Active</span>
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text)' }}>
                          Instructions: {med.instructions}
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                          <span style={{ fontSize: '11px', color: 'var(--text)' }}>Refills remaining: --</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      )}

      {/* Toast Notification */}
      {toast && (
        <div className="toast-msg" style={{ borderLeftColor: userRole === 'doctor' ? '#10B981' : '#8B5CF6' }}>
          <span>🛡️</span>
          <span>{toast}</span>
        </div>
      )}
    </div>
  );
}

const styles = {
  page: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    margin: 0,
    padding: 0,
    backgroundColor: 'var(--bg)',
    height: '100vh',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'stretch',
    color: 'var(--text)',
    boxSizing: 'border-box',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 32px',
    backgroundColor: '#111827',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    borderBottom: '4px solid #10B981',
    boxSizing: 'border-box',
    width: '100%',
    flexShrink: 0,
  },
  logoContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  logoIcon: {
    fontSize: '24px',
    color: '#10B981',
  },
  logoText: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: '0.05em',
  },
  loginForm: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  input: {
    padding: '8px 16px',
    borderRadius: '6px',
    border: '1px solid #374151',
    backgroundColor: '#1F2937',
    color: '#F9FAFB',
    fontSize: '14px',
    outline: 'none',
    minWidth: '160px',
  },
  button: {
    padding: '8px 20px',
    backgroundColor: '#10B981',
    color: '#FFFFFF',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  main: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: '15vh',
    textAlign: 'center',
    padding: '20px',
  },
  welcomeText: {
    fontSize: '48px',
    color: 'var(--text-h)',
    margin: '0 0 16px 0',
    fontWeight: '800',
    letterSpacing: '-1.5px',
  },
  subText: {
    fontSize: '18px',
    color: 'var(--text)',
    margin: 0,
  }
};
