import pandas as pd
from google import genai
from google.genai import types
import time
import json
import os
import re

# ================= CONFIGURATION =================
# Ensure your API key is set in your environment, or paste it here:
API_KEY = os.getenv("GEMINI_API_KEY") 
if not API_KEY:
    API_KEY = "YOUR_API_KEY_HERE" # Paste if not in env

INPUT_FILE = "companies.xlsx"
OUTPUT_FILE = "companies_enriched_final.xlsx"

# 1. Initialize the NEW Client (matches your successful test)
client = genai.Client(api_key=API_KEY)

# 2. Configure the Search Tool
grounding_tool = types.Tool(google_search=types.GoogleSearch())
generate_config = types.GenerateContentConfig(
    tools=[grounding_tool],
    temperature=0.1 # Keep it factual
)

def extract_json(text):
    """
    Helper to pull the JSON part out of the text response
    """
    try:
        # Try to find content between ```json and ```
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        
        # Fallback: Try to find just { ... }
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
            
    except Exception as e:
        pass
    return None

def get_company_data(name, description):
    prompt = f"""
    Perform a Google Search to find the official links for the company: "{name}"
    Context: {description}
    
    I need three specific URLs:
    1. Official Website
    2. LinkedIn Company Page
    3. Careers/Jobs Page

    Return strictly a JSON object with keys: "website", "linkedin", "careers".
    If a link is not found, use "Not Found".
    """

    try:
        # Using the NEW SDK call style
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=generate_config
        )
        
        # Parse the text response
        if response.text:
            data = extract_json(response.text)
            if data:
                return data
            
        print(f"  Warning: Could not parse JSON for {name}")
        return {"website": "Error", "linkedin": "Error", "careers": "Error"}

    except Exception as e:
        print(f"  Error processing {name}: {e}")
        return {"website": "Error", "linkedin": "Error", "careers": "Error"}

def main():
    print(f"Reading {INPUT_FILE}...")
    try:
        df = pd.read_excel(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    # Ensure columns exist
    for col in ['Website URL', 'Linkedin URL', 'Careers Page URL']:
        if col not in df.columns:
            df[col] = None

    print(f"Starting enrichment for {len(df)} companies using Gemini 2.5...")

    for index, row in df.iterrows():
        company = str(row['Company Name']).strip()
        desc = str(row.get('Company Description', '')).strip()

        if not company or company == 'nan':
            continue
        
        # Skip if already done
        if pd.notna(row['Website URL']) and str(row['Website URL']).startswith('http'):
            print(f"[{index+1}] Skipping {company} (Done)")
            continue

        print(f"[{index+1}/{len(df)}] Searching: {company}...")
        
        links = get_company_data(company, desc)
        
        df.at[index, 'Website URL'] = links.get('website', 'Not Found')
        df.at[index, 'Linkedin URL'] = links.get('linkedin', 'Not Found')
        df.at[index, 'Careers Page URL'] = links.get('careers', 'Not Found')
        
        # Save periodically
        if index % 5 == 0:
            df.to_excel(OUTPUT_FILE, index=False)
        
        time.sleep(1.5)

    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
