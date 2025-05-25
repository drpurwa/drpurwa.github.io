import os
import json
import requests
from dotenv import load_dotenv
import time # Import time for performance measurement

# Load environment variables from .env file
# This is crucial for local development to keep API keys out of your code.
# For production, environment variables would be set directly on the server.
load_dotenv()

# --- API Key Protection ---
# API keys are loaded from environment variables.
# NEVER hardcode your API keys directly in the script.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check if API key is available
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please create a .env file in the same directory as this script with:")
    print("GEMINI_API_KEY='YOUR_GEMINI_API_KEY_HERE'")
    print("Or set it directly in your system's environment variables.")
    exit(1)

# --- Utility Functions ---
# remove_semtag and levenshtein_distance are no longer needed as Snowstorm is not used for matching.

# --- API Interaction Functions ---

def call_gemini_api(clinical_text: str) -> list:
    """
    Calls the Gemini API to extract clinical entities from text and map them to SNOMED CT.
    Uses a structured response schema for consistent output.
    """
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    # Define the structured response schema for Gemini, including SNOMED CT fields directly
    response_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "text": {"type": "STRING", "description": "The exact clinical term extracted from the text."},
                "snomedCode": {"type": "STRING", "description": "The most appropriate SNOMED CT code (SCTID) for the concept. Leave empty if unsure."},
                "preferredTerm": {"type": "STRING", "description": "The SNOMED CT Preferred Term for the concept. Leave empty if unsure."},
                "semanticCategory": {"type": "STRING", "enum": ["disorder", "finding", "procedure", "observable entity", "medicinal product"], "description": "The semantic category of the concept (e.g., disorder, finding, procedure, observable entity, medicinal product)."},
                "confidenceScore": {"type": "STRING", "enum": ["High", "Medium", "Low"], "description": "Confidence in the accuracy of the extracted concept and its SNOMED mapping (High, Medium, or Low)."},
                "context": {"type": "STRING", "enum": ["present", "absent", "unknown"], "description": "The context of the term (present, absent, or unknown)."},
                "laterality": {"type": "STRING", "enum": ["left", "right", "bilateral", "N/A"], "description": "Laterality of the concept, if applicable (left, right, bilateral, or N/A)."},
                "severity": {"type": "STRING", "enum": ["mild", "moderate", "severe", "N/A"], "description": "Severity of the concept, if applicable (mild, moderate, severe, or N/A)."},
                "singularForm": {"type": "STRING", "description": "The singular form of the extracted term, if applicable."}
            },
            "required": ["text", "semanticCategory", "confidenceScore", "context"]
        }
    }

    # Prompt for Gemini to act as a medical terminology expert system
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{
                "text": f"""Anda adalah sistem pakar terminologi medis khusus yang dirancang untuk mengonversi narasi klinis berbahasa Indonesia menjadi kode SNOMED CT. Tugas Anda adalah menganalisis teks medis dan mengekstrak konsep klinis utama, lalu memetakannya ke kode SNOMED CT yang paling sesuai. Fokus pada identifikasi:
1. Diagnosis/kondisi (disorder)
2. Gejala dan temuan klinis (finding)
3. Prosedur yang dilakukan (procedure)
4. Entitas yang dapat diamati (observable entity)
5. Obat-obatan yang diberikan atau diresepkan (medicinal product)

Untuk setiap konsep yang diidentifikasi, berikan:
- Kode SNOMED CT (snomedCode)
- Istilah Pilihan SNOMED CT (preferredTerm)
- Kategori semantik (semanticCategory: disorder, finding, procedure, observable entity, medicinal product)
- Skor kepercayaan (confidenceScore: High/Medium/Low)
- Konteks (context: present/absent/unknown)
- Lateralitas (laterality: left/right/bilateral/N/A)
- Tingkat keparahan (severity: mild/moderate/severe/N/A)
- Bentuk tunggal dari istilah yang diekstrak (singularForm)

Pertahankan akurasi klinis dan utamakan spesifisitas daripada generalitas saat memilih kode.

Teks klinis: "{clinical_text}"
"""
            }]
        }],
        "generationConfig": {"responseMimeType": "application/json", "responseSchema": response_schema, "temperature": 0.2}
    }

    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        result = response.json()

        if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
            json_string = result['candidates'][0]['content']['parts'][0]['text']
            return json.loads(json_string)
        else:
            raise ValueError(f"Unexpected response structure from Gemini API: {result}")
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Gemini API request failed: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON from Gemini API: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred with Gemini API: {e}")

def process_entities(gemini_entities: list) -> list:
    """
    Processes entities extracted by Gemini, filters out those without SNOMED codes,
    and removes duplicates.
    """
    final_filtered_entities = []
    seen_texts = set()
    for entity in gemini_entities:
        # Only include entities that Gemini provided a SNOMED code for and are not duplicates
        if entity.get('snomedCode') and str(entity['snomedCode']).strip() != '' and entity.get('text') not in seen_texts:
            final_filtered_entities.append(entity)
            seen_texts.add(entity['text'])
    
    return final_filtered_entities

# --- Main Application Logic ---

def main():
    """
    Main function to run the clinical NLP application.
    Prompts for text, calls APIs, and prints results.
    """
    print("--- SNOMED CT Entity Extraction CLI ---")
    print("This application extracts clinical entities using Gemini AI and directly maps them to SNOMED CT codes.")
    print("\nSecurity Note: Your Gemini API key is loaded from an environment variable.")
    print("It is NOT hardcoded in this script, enhancing security for local execution.")
    print("--------------------------------------\n")

    clinical_text_input = input("Masukkan narasi klinis (atau tekan Enter untuk contoh default berbahasa Indonesia):\n")
    if not clinical_text_input.strip():
        clinical_text_input = "Pasien perempuan 73 tahun dibawa keluarga dengan keluhan mendadak lemah pada separuh tubuh kanan sejak 2 jam yang lalu. Pasien juga mengalami kesulitan berbicara. Riwayat hipertensi dan fibrilasi atrial."
        print(f"\nMenggunakan teks default:\n{clinical_text_input}\n")
    else:
        print(f"\nMemproses teks yang diberikan:\n{clinical_text_input}\n")

    print("Status: Menganalisis narasi klinis dengan Gemini AI...")
    start_time = time.perf_counter() # Start timing the entire process

    try:
        gemini_raw_entities = call_gemini_api(clinical_text_input)
        
        # Process and filter entities directly from Gemini's output
        processed_entities = process_entities(gemini_raw_entities)
        
        end_time = time.perf_counter() # End timing
        duration = (end_time - start_time) * 1000 # Convert to milliseconds

        print("\n--- Hasil Ekstraksi dan Pemetaan ---")
        if processed_entities:
            for i, entity in enumerate(processed_entities):
                print(f"\nEntitas {i+1}:")
                print(f"  Teks Asli:        {entity.get('text', 'N/A')}")
                print(f"  Istilah Pilihan:  {entity.get('preferredTerm', 'N/A')}")
                print(f"  Kategori Semantik: {entity.get('semanticCategory', 'N/A')}")
                print(f"  Skor Kepercayaan: {entity.get('confidenceScore', 'N/A')}")
                print(f"  Konteks:          {entity.get('context', 'N/A')}")
                print(f"  Lateralitas:      {entity.get('laterality', 'N/A')}")
                print(f"  Tingkat Keparahan: {entity.get('severity', 'N/A')}")
                print(f"  Kode SNOMED CT:   {entity.get('snomedCode', 'N/A')}")
        else:
            print("Tidak ada entitas yang diekstrak atau dipetakan dengan sukses.")
        
        print(f"\n--- Pemrosesan Selesai. Ditemukan {len(processed_entities)} entitas klinis akhir. ---")
        print(f"Waktu proses total: {duration:.2f} ms")

    except (ConnectionError, ValueError, RuntimeError) as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nTerjadi kesalahan tak terduga: {e}")

if __name__ == "__main__":
    main()
