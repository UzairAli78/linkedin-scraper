# 💼 linkedin-scraper

A LinkedIn job scraping and AI summarization tool with two usage modes: a **Streamlit web UI** (`linkedin_app.py`) and a **CLI pipeline** (`scraper.py` → `summarizer.py`). Scraped jobs are saved to a single Excel file — `linkedin_jobs_summarized.xlsx` — ready to open in Google Sheets.

---

## 📁 Project Structure

```
linkedin-scraper/
├── linkedin_app.py            # Streamlit web app (all-in-one UI)
├── scraper.py                 # CLI scraper using Selenium + ChromeDriver
├── summarizer.py              # CLI AI summarizer (reads/writes the .xlsx)
├── linkedin_requirements.txt  # Python dependencies
└── linkedin_jobs_summarized.xlsx  # Output file (auto-generated)
```

---

## ✨ Features

- Scrape LinkedIn job listings without requiring login
- Auto-converts logged-in LinkedIn URLs to the public-facing format
- Extracts job title, company, location, job link, and posted date
- Generates AI summaries using the free Hugging Face `facebook/bart-large-cnn` model
- Exports results to `.xlsx` (compatible with Google Sheets)
- Two modes: interactive **Streamlit UI** or headless **CLI pipeline**

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r linkedin_requirements.txt
```

> **CLI mode only** (using `scraper.py`) additionally requires:
> - Google Chrome installed
> - `selenium` and a matching `chromedriver`

---

### 2a. Run the Streamlit Web App (Recommended)

```bash
streamlit run linkedin_app.py
```

Then open your browser at `http://localhost:8501` and:

1. Paste a LinkedIn job search URL into the input box
2. Click **🚀 Scrape Jobs**
3. Click **🤖 Generate AI Summaries**
4. Click **📥 Download as Google Sheets (.xlsx)**

---

### 2b. Run the CLI Pipeline

**Step 1 — Scrape jobs:**

```bash
python scraper.py
```

You'll be prompted for:
- A LinkedIn job search URL (or press Enter to use the default)
- How many jobs to scrape (default: 10)

Results are saved to `linkedin_jobs_summarized.xlsx`.

**Step 2 — Add AI summaries:**

```bash
python summarizer.py
```

Reads `linkedin_jobs_summarized.xlsx`, fills in the `Job Summary` column using the Hugging Face API, and saves the file back in place.

---

## 📋 Output Format

Both modes produce a single Excel file with the following columns:

| Column | Description |
|---|---|
| `Job Title` | Position name |
| `Company` | Hiring company |
| `Location` | Job location |
| `Job Link` | Direct URL to the job posting |
| `Posted Date` | Date the listing was posted |
| `Job Summary` | AI-generated summary (filled after summarizer runs) |

---

## 🔗 Supported URL Formats

Any LinkedIn jobs search URL works. Logged-in session URLs are automatically converted to the public format. Examples:

```
https://www.linkedin.com/jobs/search?keywords=python&location=United+States
https://www.linkedin.com/jobs/search/?keywords=data+engineer&geoId=103644278
```

---

## ⚙️ How It Works

### Streamlit App (`linkedin_app.py`)
- Uses `requests` + `BeautifulSoup` — no browser or login needed
- Parses job cards using CSS selectors (`div.base-card`, `div.job-search-card`, etc.)
- Falls back across multiple selector variants to handle LinkedIn's frequent HTML changes
- AI summaries are generated inline via the Hugging Face Inference API

### CLI Scraper (`scraper.py`)
- Uses `Selenium` with a headless Chrome instance
- Scrolls the page to trigger lazy-loaded content
- Applies the same multi-selector fallback strategy as the Streamlit app

### Summarizer (`summarizer.py`)
- Reads the scraped `.xlsx` file
- Builds a short job description string per row and sends it to `facebook/bart-large-cnn`
- Writes summaries back to the `Job Summary` column with a 1.5-second delay between calls to avoid rate limits

---

## ⚠️ Notes & Limitations

- **No login required**, but LinkedIn may rate-limit or block repeated requests. Use responsibly.
- The Hugging Face free inference API can be slow or unavailable during peak hours. The summarizer falls back to a plain-text description if the API call fails.
- LinkedIn frequently changes its HTML structure — if no jobs are scraped, the CSS selectors in `scrape_jobs()` / `scrape_linkedin_jobs()` may need updating.
- The Selenium-based `scraper.py` requires Chrome and a compatible `chromedriver` binary on your system PATH.

---

## 📦 Dependencies

```
streamlit
pandas
requests
beautifulsoup4
openpyxl
```

> CLI mode also requires: `selenium`

---

## 📂 Opening Results in Google Sheets

1. Go to [sheets.google.com](https://sheets.google.com)
2. Click **File → Import**
3. Upload `linkedin_jobs_summarized.xlsx`
4. Select **Replace spreadsheet** and click **Import data**
