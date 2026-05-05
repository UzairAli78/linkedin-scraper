"""
LinkedIn Job Summarizer
Reads linkedin_jobs_summarized.xlsx, fills the Job Summary column, saves back.
Run AFTER scraper.py
"""

import pandas as pd
import requests
import time

FILE = 'linkedin_jobs_summarized.xlsx'


def get_ai_summary(job_title, company, location):
    """Call free Hugging Face summarization model"""
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

    job_text = (
        f"Job Position: {job_title} at {company} located in {location}. "
        "This is a full-time position in the United States."
    )

    try:
        resp = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"inputs": job_text, "parameters": {"max_length": 60, "min_length": 20}},
            timeout=15
        )
        if resp.status_code == 200:
            result = resp.json()
            if isinstance(result, list) and result:
                summary = result[0].get('summary_text', '').strip()
                if summary:
                    return summary
        return f"{job_title} position at {company} in {location}."
    except Exception as e:
        print(f"  ⚠️  API error: {e}")
        return f"{job_title} at {company}, {location}."


def add_summaries():
    print("=" * 60)
    print("         AI JOB SUMMARIZER")
    print("=" * 60)

    try:
        df = pd.read_excel(FILE, engine='openpyxl')
    except FileNotFoundError:
        print(f"\n❌ {FILE} not found!")
        print("💡 Run scraper.py first.")
        return False
    except Exception as e:
        print(f"\n❌ Error reading file: {e}")
        return False

    total = len(df)
    print(f"\n📊 {total} jobs found in {FILE}")
    print("🤖 Generating summaries…\n")

    for idx, row in df.iterrows():
        title    = str(row.get('Job Title', ''))
        company  = str(row.get('Company', ''))
        location = str(row.get('Location', ''))

        print(f"  [{idx + 1}/{total}] {title} @ {company}")
        summary = get_ai_summary(title, company, location)
        df.at[idx, 'Job Summary'] = summary
        print(f"         → {summary}\n")

        time.sleep(1.5)   # avoid rate-limit

    # Save back to THE SAME file
    df.to_excel(FILE, index=False, sheet_name='LinkedIn Jobs', engine='openpyxl')

    print("=" * 60)
    print(f"✅ All summaries saved → {FILE}")
    print("📂 Open it directly in Google Sheets (File → Import)")
    print("=" * 60)

    print("\n📋 PREVIEW:\n")
    print(df[['Job Title', 'Company', 'Job Summary']].head(5).to_string())
    return True


if __name__ == "__main__":
    success = add_summaries()
    if not success:
        print("\n❌ Summarizer failed. Check errors above.")