"""
LinkedIn Job Scraper & AI Summarizer - Streamlit UI
Uses requests + BeautifulSoup (no login required, no headless browser blocks)
Single output file: linkedin_jobs_summarized.xlsx
"""

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import io
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# ── Page config ───────────────────────────────
st.set_page_config(page_title="LinkedIn Job Scraper", page_icon="💼", layout="wide")

st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #0077B5 0%, #00A0DC 100%);}
    h1 {color: white; text-align: center;}
    .stButton>button {
        background-color: #0077B5;
        color: white;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("💼 LinkedIn Job Scraper & AI Summarizer")
st.markdown("---")


# ══════════════════════════════════════════════
#  URL HELPER — converts any LinkedIn jobs URL
#  to the public scrapable format
# ══════════════════════════════════════════════
def to_public_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    if "linkedin.com/jobs/search" in raw_url and "search-results" not in raw_url:
        return raw_url

    parsed = urlparse(raw_url)
    qs = parse_qs(parsed.query)

    keywords = qs.get("keywords", [""])[0]
    location = qs.get("location", ["United States"])[0]
    geo_id   = qs.get("geoId",    ["103644278"])[0]

    params = {
        "keywords": keywords,
        "location": location,
        "geoId":    geo_id,
        "f_JT":     "F",
        "position": "1",
        "pageNum":  "0",
    }
    return urlunparse(("https", "www.linkedin.com", "/jobs/search/", "", urlencode(params), ""))


# ══════════════════════════════════════════════
#  SCRAPER  (requests + BeautifulSoup)
# ══════════════════════════════════════════════
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}


def _text(tag, selectors):
    for sel in selectors:
        el = tag.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return ""


def _attr(tag, selectors, attr):
    for sel in selectors:
        el = tag.select_one(sel)
        if el and el.get(attr):
            return el[attr]
    return "N/A"


def scrape_jobs(url: str, max_jobs: int) -> list:
    public_url = to_public_url(url)
    jobs_data  = []

    try:
        resp = requests.get(public_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        st.error(f"❌ Could not reach LinkedIn: {e}")
        return []

    soup  = BeautifulSoup(resp.text, "html.parser")
    cards = (
        soup.select("div.base-card")
        or soup.select("div.job-search-card")
        or soup.select("ul.jobs-search__results-list li")
    )

    if not cards:
        return []

    for card in cards[:max_jobs]:
        title    = _text(card, ["h3.base-search-card__title", "h3.job-search-card__title"])
        company  = _text(card, ["h4.base-search-card__subtitle", "h4.job-search-card__company-name", "a.hidden-nested-link"])
        location = _text(card, ["span.job-search-card__location", "span.job-card-container__metadata-item"])
        job_link = _attr(card, ["a.base-card__full-link", "a.job-card-list__title"], "href")
        posted   = ""
        t = card.select_one("time")
        if t:
            posted = t.get("datetime", t.get_text(strip=True))

        if not title and not company:
            continue

        jobs_data.append({
            "Job Title":   title,
            "Company":     company,
            "Location":    location,
            "Job Link":    job_link,
            "Posted Date": posted,
            "Job Summary": "",
        })

    return jobs_data


# ══════════════════════════════════════════════
#  AI SUMMARIZER
# ══════════════════════════════════════════════
def get_ai_summary(job_title, company, location):
    API_URL  = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    job_text = (
        f"Job Position: {job_title} at {company} located in {location}. "
        "This is a full-time position in the United States."
    )
    try:
        resp = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"inputs": job_text, "parameters": {"max_length": 60, "min_length": 20}},
            timeout=15,
        )
        if resp.status_code == 200:
            result = resp.json()
            if isinstance(result, list) and result:
                s = result[0].get("summary_text", "").strip()
                if s:
                    return s
    except Exception:
        pass
    return f"{job_title} position at {company} in {location}."


# ══════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ Settings")
    max_jobs = st.slider("Number of jobs to scrape", 5, 50, 10)
    st.markdown("---")
    st.info(
        "**How to use:**\n"
        "1. Paste LinkedIn job search URL\n"
        "2. Click **Scrape Jobs**\n"
        "3. Click **Generate Summaries**\n"
        "4. Download as Google Sheets (.xlsx)"
    )
    st.markdown("---")
    st.caption(
        "💡 **Best URL format:**\n\n"
        "`linkedin.com/jobs/search?keywords=python`\n\n"
        "Logged-in URLs are auto-converted to the public format."
    )


# ══════════════════════════════════════════════
#  MAIN UI
# ══════════════════════════════════════════════
st.subheader("📎 Step 1: Paste LinkedIn Job Search URL")

linkedin_url = st.text_input(
    "Enter LinkedIn URL",
    placeholder="https://www.linkedin.com/jobs/search?keywords=python&location=United+States",
    help="Paste any LinkedIn jobs URL — logged-in or public.",
)

if not linkedin_url:
    linkedin_url = (
        "https://www.linkedin.com/jobs/search/?keywords=&location=United%20States"
        "&geoId=103644278&f_JT=F&f_E=2&f_PP=102571732"
    )

converted = to_public_url(linkedin_url)
if converted != linkedin_url.strip():
    st.info(f"🔄 Converted to public URL:\n`{converted}`")

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Scrape Jobs", use_container_width=True):
        with st.spinner(f"Scraping up to {max_jobs} jobs…"):
            jobs = scrape_jobs(linkedin_url, max_jobs)

        if jobs:
            st.session_state.jobs_df = pd.DataFrame(jobs)
            st.success(f"✅ Scraped {len(jobs)} jobs successfully!")
            st.dataframe(st.session_state.jobs_df, use_container_width=True)
        else:
            st.error(
                "❌ No jobs found.\n\n"
                "Try this example URL:\n"
                "`https://www.linkedin.com/jobs/search/?keywords=software+engineer&location=United+States`"
            )

with col2:
    if st.button("🤖 Generate AI Summaries", use_container_width=True):
        if "jobs_df" in st.session_state:
            df       = st.session_state.jobs_df
            progress = st.progress(0)
            status   = st.empty()

            for idx, row in df.iterrows():
                status.text(f"Summarizing {idx + 1} of {len(df)}…")
                df.at[idx, "Job Summary"] = get_ai_summary(
                    row["Job Title"], row["Company"], row["Location"]
                )
                progress.progress((idx + 1) / len(df))
                time.sleep(1)

            st.session_state.jobs_df = df
            status.empty()
            st.success("✅ All summaries generated!")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("⚠️ Please scrape jobs first!")

# ══════════════════════════════════════════════
#  DOWNLOAD — single .xlsx
# ══════════════════════════════════════════════
if "jobs_df" in st.session_state:
    st.markdown("---")
    st.subheader("💾 Download Results")

    df     = st.session_state.jobs_df
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="LinkedIn Jobs")
    buffer.seek(0)

    st.download_button(
        label="📥 Download as Google Sheets (.xlsx)",
        data=buffer,
        file_name="linkedin_jobs_summarized.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("📊 Results Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Jobs",       len(df))
    c2.metric("Unique Companies", df["Company"].nunique())
    c3.metric("Unique Locations", df["Location"].nunique())

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:white;'>💼 LinkedIn Job Scraper | BeautifulSoup + AI + Google Sheets</p>",
    unsafe_allow_html=True,
)