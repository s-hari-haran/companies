# Company Data Enrichment Tool

Automated tool to enrich company datasets with official URLs (website, LinkedIn, careers pages, and job listings) using Google's Gemini 2.5 Flash API with Google Search grounding.

## Features

- **Automated URL Discovery**: Finds official website, LinkedIn, careers page, and job listings URLs
- **Google Search Integration**: Uses Gemini 2.5 Flash with real-time Google Search for accurate results
- **Resume Support**: Skips already-processed rows to resume interrupted runs
- **Periodic Saves**: Auto-saves progress every 5 rows to prevent data loss
- **Smart JSON Parsing**: Extracts structured data from AI responses

## Files

- `enrich_gemini_code.py` - Main enrichment script (3 URLs: website, LinkedIn, careers)
- `final_code.py` - Enhanced version (4 URLs: adds job listings/ATS detection)
- `companies.xlsx` - Input dataset with company names and descriptions
- `companies_enriched_final.xlsx` - Output with enriched company data
- `requirements.txt` - Python dependencies
- `.env` - API key configuration (gitignored)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Set your Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY='your-api-key-here'
```

Or add it to `.env`:
```
GEMINI_API_KEY=your-api-key-here
```

### 3. Prepare Input File

Ensure `companies.xlsx` contains columns:
- `Company Name` (required)
- `Company Description` (optional, improves accuracy)

## Usage

### Basic Enrichment (3 URLs)

```bash
python enrich_gemini_code.py
```

Outputs: `companies_enriched_final.xlsx` with:
- Website URL
- LinkedIn URL  
- Careers Page URL

### Enhanced Enrichment (4 URLs)

```bash
python final_code.py
```

Outputs: `companies_final_complete.xlsx` with:
- Website URL
- LinkedIn URL
- Careers Page URL
- **Job Listings URL** (detects ATS platforms like Greenhouse, Lever, Workday, etc.)

## How It Works

1. **Reads** company data from Excel file
2. **Skips** rows with existing URLs (resume capability)
3. **Sends** structured prompts to Gemini 2.5 Flash with Google Search tool
4. **Extracts** JSON responses with company URLs
5. **Saves** progress periodically (every 5 rows)
6. **Outputs** enriched dataset to Excel

## Configuration

Edit script constants to customize:

```python
INPUT_FILE = "companies.xlsx"           # Input filename
OUTPUT_FILE = "companies_enriched_final.xlsx"  # Output filename
temperature = 0.1                       # Lower = more factual
time.sleep(1.5)                        # Rate limiting delay (seconds)
```

## Rate Limiting

Scripts include `time.sleep()` delays between API calls to:
- Stay within free tier quota
- Avoid rate limit errors
- Ensure sustainable batch processing

## Error Handling

- **Parse errors**: Returns `"Error"` for that company
- **Missing data**: Returns `"Not Found"` for unavailable URLs
- **Network issues**: Prints error and continues to next row
- **File errors**: Clear error messages with troubleshooting hints

## Change Tracking

Use included comparison script to audit changes:

```bash
python - <<'PY'
# (comparison script shown earlier)
PY
```

Outputs: `companies_change_report.csv` with before/after values for each cell.

## Requirements

- Python 3.8+
- pandas
- openpyxl
- google-genai (Gemini SDK)

## Security Notes

- `.env` is gitignored to protect API keys
- Never commit API keys to version control
- Rotate keys after sharing or if exposed

## License

MIT

## Support

For issues or questions, open a GitHub issue.
