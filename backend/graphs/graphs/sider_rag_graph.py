#!/usr/bin/env python3
import os
import re
import sys
import shutil
from typing import TypedDict, List

# Ensure we import our LLM properly
try:
    from llm import llm
except ImportError:
    print("Error: Could not import 'llm' from llm.py. Make sure llm.py is in the current directory.")
    sys.exit(1)

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END

CHROMA_DB_DIR = "./chroma_db"
COLLECTION_NAME = "sider_collection"
DATA_FILE = "./SIDER_Metadata/sider_rag_summaries.txt"


def initialize_embeddings(
    better_model: str = "sentence-transformers/all-mpnet-base-v2",
    fallback_model: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> HuggingFaceEmbeddings:
    """
    Tries to load the better model locally.
    If not cached, downloads it from HuggingFace.
    Falls back to a smaller, locally cached model if offline or downloads fail.
    """
    print(f"Attempting to load better embedding model '{better_model}' from local cache...")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=better_model,
            model_kwargs={"local_files_only": True}
        )
        print(f"Successfully loaded '{better_model}' from local cache.")
        return embeddings
    except Exception as e:
        print(f"'{better_model}' not found locally or failed to load offline: {e}")
        
    print(f"Attempting to download better embedding model '{better_model}' from HuggingFace...")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=better_model,
            model_kwargs={"local_files_only": False}
        )
        print(f"Successfully downloaded and loaded '{better_model}'.")
        return embeddings
    except Exception as e:
        print(f"Failed to download '{better_model}': {e}")
        
    print(f"Falling back to local fallback model '{fallback_model}'...")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=fallback_model,
            model_kwargs={"local_files_only": True}
        )
        print(f"Successfully loaded fallback model '{fallback_model}' locally.")
        return embeddings
    except Exception as e:
        print(f"Failed to load fallback model locally ({e}). Downloading '{fallback_model}'...")
        embeddings = HuggingFaceEmbeddings(
            model_name=fallback_model,
            model_kwargs={"local_files_only": False}
        )
        print(f"Successfully loaded fallback model '{fallback_model}'.")
        return embeddings

def load_and_chunk_data(file_path: str) -> List[Document]:
    """
    Custom chunking strategy: Parses SIDER drug records by spliting on START/END record boundaries.
    This guarantees that each chunk contains exactly one complete drug record (including its medicine name,
    category breakdown, and key risks summary) rather than splitting a drug record in half.
    """
    if not os.path.exists(file_path):
        print(f"Error: Data file '{file_path}' not found. Please run summarize_sider.py first to generate it.")
        sys.exit(1)

    print(f"Loading and chunking data from '{file_path}'...")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by the START DRUG RECORD delimiter
    raw_records = content.split("--- START DRUG RECORD ---")
    documents = []
    
    for record in raw_records:
        record = record.strip()
        if not record:
            continue
        
        # Strip the trailing END DRUG RECORD delimiter if it exists
        if "--- END DRUG RECORD ---" in record:
            record = record.split("--- END DRUG RECORD ---")[0].strip()
        
        # Extract medicine name for metadata
        match = re.search(r"Medicine Name:\s*(.*)", record)
        metadata = {}
        if match:
            metadata["medicine_name"] = match.group(1).strip()
        else:
            metadata["medicine_name"] = "Unknown"
            
        documents.append(Document(page_content=record, metadata=metadata))

    print(f"Successfully loaded {len(documents)} complete drug records as chunks.")
    return documents


embeddings = initialize_embeddings()

# Check if Chroma DB directory exists and is newer than source file
rebuild = False
if os.path.exists(CHROMA_DB_DIR):
    if os.path.getmtime(DATA_FILE) > os.path.getmtime(CHROMA_DB_DIR):
        print(f"Source file '{DATA_FILE}' has been modified. Rebuilding Chroma DB...")
        try:
            shutil.rmtree(CHROMA_DB_DIR)
        except Exception as e:
            print(f"Warning: Could not clear directory {CHROMA_DB_DIR}: {e}")
        rebuild = True
    else:
        print(f"Loading vector store index from local Chroma DB cache '{CHROMA_DB_DIR}'...")
else:
    print("Vector store index not found on disk. Building Chroma DB...")
    rebuild = True

if rebuild:
    chunks = load_and_chunk_data(DATA_FILE)
    # Chroma automatically saves to disk when persist_directory is specified
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DB_DIR
    )
    print("Chroma DB built and saved successfully to disk.\n")
else:
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    print("Vector store loaded successfully from Chroma DB.\n")

# Load data and add to the vector store
# chunks = load_and_chunk_data(DATA_FILE)
# vector_store.add_documents(chunks)


class SiderRAGState(TypedDict):
    query: str
    documents: List[Document]
    generation: str


def retrieve(state: SiderRAGState) -> dict:
    """Retrieve relevant drug documents from the vector store."""
    query = state["query"]
    # Retrieve top 3 most relevant drug records
    retrieved_docs = vector_store.similarity_search(query, k=5)
    retrieved_names = [doc.metadata.get("medicine_name", "Unknown") for doc in retrieved_docs]
    print(f"[Node: Retrieve] Retrieved records for: {', '.join(retrieved_names)}")
    return {"documents": retrieved_docs}


def generate(state: SiderRAGState) -> dict:
    """Generate an answer using the retrieved context and the user query."""
    query = state["query"]
    docs = state["documents"]

    # Format the retrieved documents as context
    context = "\n\n".join([doc.page_content for doc in docs])

    # Construct chat prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert pharmacological AI assistant. Use the following retrieved SIDER drug record "
            "contexts to answer the query. If you dont get details for all the drugs, provide information for whatever drug you recieved."
            "Retrieved SIDER Database Context:\n"
            "===================================\n"
            "{context}\n"
            "===================================\n\n"
            "Provide a clear, accurate, and concise answer based strictly on the retrieved records. "
            "Include concise details about side effects for each medicine"
            "MAX WORD LIMIT: 512"
            "Do not make up facts or side effects not present in the context."
        )),
        ("user", "{query}")
    ])

    # Chain definition
    chain = prompt_template | llm | StrOutputParser()
    
    # Run chain
    response = chain.invoke({"context": context, "query": query})
    return {"generation": response}

# Construct the LangGraph StateGraph
print("Building LangGraph RAG Graph...")
builder = StateGraph(SiderRAGState)

# Add nodes
builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)

# Connect nodes
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

# Compile the graph
sider_graph = builder.compile()
