import pandas as pd
from google import genai
from google.genai import types
import time
import json
import os
import re

# ================= CONFIGURATION =================
# 1. API KEY SETUP
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    # PASTE YOUR NEW KEY HERE
    API_KEY = "YOUR_NEW_API_KEY_HERE" 

# 2. FILE SETUP
# We read your existing progress
INPUT_FILE = "companies_final_complete.xlsx"
# We save to the NEW requested filename
OUTPUT_FILE = "copy_88_150.xlsx"

# 3. INITIALIZE GEMINI (New SDK)
client = genai.Client(api_key=API_KEY)

grounding_tool = types.Tool(google_search=types.GoogleSearch())
generate_config = types.GenerateContentConfig(
    tools=[grounding_tool],
    temperature=0.1
)

def extract_json(text):
    """ Helper to extract JSON from the AI's response text """
    try:
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match: return json.loads(match.group(1))
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match: return json.loads(match.group(1))
    except: pass
    return None

def get_detailed_links(name, description):
    prompt = f"""
    Perform a Google Search to find official links for: "{name}"
    Context: {description}
    
    I need 4 specific URLs.
    
    1. **Official Website**: Main homepage.
    2. **LinkedIn Company Page**: Main LinkedIn profile.
    3. **Careers Page**: The "marketing" page on their site (e.g., "Join Us", "Life at {name}").
    4. **Job Listings URL**: The direct link where specific open roles are listed. 
       - **Look for ATS domains** (e.g., myworkdayjobs, greenhouse, lever, ashby, bambooHR, zohorecruit, workable, smartrecruiters, icims, jobvite).
       - **Look for internal boards** (e.g., company.com/careers/openings).
       - **Fallback**: If no official board exists, use their LinkedIn Jobs tab or Glassdoor/Indeed page.

    Note: If the "Careers Page" and "Job Listings" are the same URL, use the same URL for both.

    Return JSON with keys: "website", "linkedin", "careers", "job_listings".
    If not found, use "Not Found".
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=generate_config
        )
        data = extract_json(response.text)
        if data: return data
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    print(f"Reading {INPUT_FILE}...")
    try:
        df = pd.read_excel(INPUT_FILE)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: Could not find {INPUT_FILE}.")
        return

    # Ensure all 4 columns exist
    cols = ['Website URL', 'Linkedin URL', 'Careers Page URL', 'Job Listings URL']
    for col in cols:
        if col not in df.columns:
            df[col] = None

    print(f"Processing {len(df)} rows...")
    print("Mode: Processing Rows 1 to 150 (Backfilling 1-87, New search 88-150).")

    for index, row in df.iterrows():
        # --- STOP LOGIC ---
        # Stop processing if we go past Row 150 (Index 149)
        if index >= 150:
            print("Reached Row 150. Stopping.")
            break
        # ------------------

        company = str(row['Company Name']).strip()
        desc = str(row.get('Company Description', '')).strip()

        if not company or company == 'nan': continue
        
        # --- SMART LOGIC ---
        has_website = pd.notna(row['Website URL']) and str(row['Website URL']).startswith('http')
        has_jobs = pd.notna(row['Job Listings URL']) and str(row['Job Listings URL']).startswith('http')
        
        # If we have EVERYTHING (Website + Job Listings), we skip.
        if has_website and has_jobs:
            print(f"[{index+1}] Skipping {company} (Fully Done)")
            continue

        print(f"[{index+1}/{len(df)}] Searching: {company}...")
        
        links = get_detailed_links(company, desc)
        
        if links:
            # If we don't have a website (Rows 88-150), save it.
            if not has_website:
                df.at[index, 'Website URL'] = links.get('website', 'Not Found')
                df.at[index, 'Linkedin URL'] = links.get('linkedin', 'Not Found')
            
            # Always update these (Fixes Rows 1-87 missing jobs + Fills Rows 88-150)
            df.at[index, 'Careers Page URL'] = links.get('careers', 'Not Found')
            df.at[index, 'Job Listings URL'] = links.get('job_listings', 'Not Found')
            
            print(f"  -> Found Job Board: {links.get('job_listings')}")
        else:
            print("  -> Failed to find data.")

        # Save every 5 rows
        if index % 5 == 0:
            df.to_excel(OUTPUT_FILE, index=False)
        
        # FAST DELAY (2 seconds)
        time.sleep(2)

    # Final Save
    df.to_excel(OUTPUT_FILE, index=False)
    print("------------------------------------------------")
    print(f"DONE! Your final file is: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()