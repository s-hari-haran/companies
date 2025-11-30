import pandas as pd
import google.generativeai as genai
import time
import json

# ================= CONFIGURATION =================
# PASTE YOUR API KEY HERE
API_KEY = "gemini-api-key" 

# File names
INPUT_FILE = "companies.xlsx" # Make sure this matches your file name exactly
OUTPUT_FILE = "enriched_data.xlsx"

# Configure Gemini
genai.configure(api_key=API_KEY)
# Use Gemini 1.5 Flash - it is fast, cheap/free, and has Google Search built-in
model = genai.GenerativeModel('gemini-1.5-flash', tools='google_search_retrieval')

def get_company_links(name, description):
    """
    Asks Gemini to find specific URLs using the company name AND description for accuracy.
    """
    prompt = f"""
    Perform a Google Search to find the official links for the following company:
    
    Company Name: {name}
    Context/Description: {description}
    
    I need three specific URLs:
    1. The official Website URL
    2. The official LinkedIn Company Page URL
    3. The direct Careers or Jobs page URL on their site (or their ATS like Lever/Greenhouse)

    Return the result strictly as a JSON object with keys: "website", "linkedin", "careers".
    If a link is not found, set the value to "Not Found".
    Do not add markdown formatting like ```json.
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean up response to ensure it's valid JSON
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_text)
    except Exception as e:
        print(f"  Error processing {name}: {e}")
        return {"website": "Error", "linkedin": "Error", "careers": "Error"}

def main():
    print(f"Loading {INPUT_FILE}...")
    try:
        df = pd.read_excel(INPUT_FILE)
    except FileNotFoundError:
        print("Error: File not found. Please check the file name in the script.")
        return

    # Create columns if they don't exist yet (matching your screenshot headers)
    # Using specific column names from your image
    target_cols = ['Website URL', 'Linkedin URL', 'Careers Page URL']
    for col in target_cols:
        if col not in df.columns:
            df[col] = None

    print(f"Found {len(df)} rows. Starting enrichment...")

    # Iterate through the data
    for index, row in df.iterrows():
        company_name = str(row['Company Name']).strip()
        description = str(row['Company Description']).strip()
        
        # Skip empty rows or rows that look like headers/examples
        if not company_name or company_name.lower() == 'nan':
            continue

        # Skip rows that already have a Website URL filled in (like Row 2 and 3 in your image)
        # This saves time and API credits!
        if pd.notna(row['Website URL']) and str(row['Website URL']).startswith('http'):
            print(f"[{index+1}] Skipping {company_name} (Already done)")
            continue

        print(f"[{index+1}/{len(df)}] Searching for: {company_name}...")
        
        # Call Gemini
        links = get_company_links(company_name, description)
        
        # Update the DataFrame
        df.at[index, 'Website URL'] = links.get('website', '')
        df.at[index, 'Linkedin URL'] = links.get('linkedin', '')
        df.at[index, 'Careers Page URL'] = links.get('careers', '')

        # Save periodically (every 5 rows) just in case script crashes
        if index % 5 == 0:
            df.to_excel(OUTPUT_FILE, index=False)
        
        # Sleep to be nice to the API (avoid hitting rate limits)
        time.sleep(4)

    # Final Save
    df.to_excel(OUTPUT_FILE, index=False)
    print("------------------------------------------------")
    print(f"Success! Enriched data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()