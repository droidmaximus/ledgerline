#!/usr/bin/env python3
"""Ingest PDF documents into PageIndex system"""

import os
import sys
from pathlib import Path
import requests
import json

INGESTION_URL = "http://localhost:8080"
DOCUMENT_DIR = Path("sample-data")
TIMEOUT = 60

def check_service():
    """Verify ingestion service is healthy"""
    try:
        resp = requests.get(f"{INGESTION_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("[OK] Ingestion Service is HEALTHY")
            return True
        else:
            print(f"[FAIL] Service returned status {resp.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Cannot reach {INGESTION_URL}: {e}")
        return False

def ingest_documents():
    """Upload all PDFs from sample-data directory"""
    
    print("")
    print("=" * 60)
    print("  PageIndex Document Ingestion")
    print("=" * 60)
    print("")
    
    # Check service health
    print("Checking ingestion service health...")
    if not check_service():
        return False
    
    # Find PDFs
    if not DOCUMENT_DIR.exists():
        print(f"[FAIL] Directory not found: {DOCUMENT_DIR}")
        return False
    
    pdf_files = list(DOCUMENT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[WARNING] No PDFs found in {DOCUMENT_DIR}")
        return False
    
    print(f"Found {len(pdf_files)} PDF(s):")
    for pdf in pdf_files:
        size_kb = pdf.stat().st_size / 1024
        print(f"  - {pdf.name} ({size_kb:.1f} KB)")
    print("")
    
    # Upload each PDF
    success_count = 0
    failure_count = 0
    uploaded_docs = []
    
    for pdf in pdf_files:
        print(f"Uploading: {pdf.name}...", end=" ")
        
        try:
            with open(pdf, "rb") as f:
                files = {"file": f}
                resp = requests.post(
                    f"{INGESTION_URL}/documents/upload",
                    files=files,
                    timeout=TIMEOUT
                )
            
            if resp.status_code == 200:
                data = resp.json()
                doc_id = data.get("doc_id")
                print(f"[OK]")
                print(f"  Doc ID: {doc_id}")
                success_count += 1
                uploaded_docs.append({
                    "filename": pdf.name,
                    "doc_id": doc_id
                })
            else:
                print(f"[FAIL] Status {resp.status_code}")
                failure_count += 1
                
        except Exception as e:
            print(f"[ERROR] {e}")
            failure_count += 1
    
    # Summary
    print("")
    print("=" * 60)
    print("  Ingestion Summary")
    print("=" * 60)
    print(f"Uploaded: {success_count}")
    print(f"Failed: {failure_count}")
    print("")
    
    if uploaded_docs:
        print("Document IDs (save these for querying):")
        for doc in uploaded_docs:
            print(f"  {doc['filename']}: {doc['doc_id']}")
        print("")
    
    print("Documents are now processing in the backend.")
    print("Parser service will generate tree structures.")
    print("")
    
    return success_count > 0

if __name__ == "__main__":
    success = ingest_documents()
    sys.exit(0 if success else 1)
