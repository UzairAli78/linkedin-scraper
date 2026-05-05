"""
LinkedIn Job Scraper
Scrapes jobs and saves to linkedin_jobs_summarized.xlsx
Run this first, then run summarizer.py
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

OUTPUT_FILE = 'linkedin_jobs_summarized.xlsx'


def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    driver = webdriver.Chrome(options=options)
    return driver


def scrape_linkedin_jobs(url, max_jobs=10):
    print("=" * 60)
    print("         LINKEDIN JOB SCRAPER")
    print("=" * 60)
    print(f"📍 URL    : {url}")
    print(f"🎯 Target : {max_jobs} jobs\n")

    driver = setup_driver()
    jobs_data = []

    try:
        driver.get(url)
        time.sleep(5)
        print("✅ Page loaded")

        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # Try multiple card selectors (LinkedIn changes them often)
        job_cards = []
        for sel in ['div.base-card', 'li.jobs-search-results__list-item', 'div.job-search-card']:
            job_cards = driver.find_elements(By.CSS_SELECTOR, sel)
            if job_cards:
                print(f"✅ Found {len(job_cards)} cards using selector: {sel}")
                break

        job_cards = job_cards[:max_jobs]

        for idx, card in enumerate(job_cards, 1):
            try:
                title = _find_text(card, [
                    'h3.base-search-card__title',
                    'h3.job-search-card__title',
                    'a.job-card-list__title',
                ])
                company = _find_text(card, [
                    'h4.base-search-card__subtitle',
                    'h4.job-search-card__company-name',
                    'a.job-card-container__company-name',
                ])
                location = _find_text(card, [
                    'span.job-search-card__location',
                    'li.job-search-card__location',
                    'span.job-card-container__metadata-item',
                ])
                job_link = _find_attr(card, [
                    'a.base-card__full-link',
                    'a.job-card-list__title',
                    'a.job-card-container__link',
                ], 'href')

                posted_date = "N/A"
                try:
                    posted_date = card.find_element(By.CSS_SELECTOR, 'time').get_attribute('datetime')
                except:
                    pass

                if not title and not company:
                    continue

                jobs_data.append({
                    'Job Title': title,
                    'Company': company,
                    'Location': location,
                    'Job Link': job_link,
                    'Posted Date': posted_date,
                    'Job Summary': ''   # filled by summarizer.py
                })
                print(f"  ✅ Job {idx}: {title} @ {company}")

            except Exception as e:
                print(f"  ⚠️  Job {idx} skipped: {e}")
                continue

    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        driver.quit()

    if jobs_data:
        df = pd.DataFrame(jobs_data)
        df.to_excel(OUTPUT_FILE, index=False, sheet_name='LinkedIn Jobs', engine='openpyxl')
        print(f"\n✅ Saved {len(jobs_data)} jobs → {OUTPUT_FILE}")
        print("🎯 Next: run summarizer.py to fill in Job Summary column")
    else:
        print("\n❌ No jobs scraped. Try a different URL or log into LinkedIn first.")

    return len(jobs_data)


# ── helpers ──────────────────────────────────
def _find_text(card, selectors):
    from selenium.webdriver.common.by import By
    for sel in selectors:
        try:
            text = card.find_element(By.CSS_SELECTOR, sel).text.strip()
            if text:
                return text
        except:
            continue
    return ""


def _find_attr(card, selectors, attr):
    from selenium.webdriver.common.by import By
    for sel in selectors:
        try:
            val = card.find_element(By.CSS_SELECTOR, sel).get_attribute(attr)
            if val:
                return val
        except:
            continue
    return "N/A"


# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("     LINKEDIN JOB SCRAPER")
    print("=" * 60)

    linkedin_url = input("\n📎 Paste LinkedIn job search URL: ").strip()
    if not linkedin_url:
        linkedin_url = (
            "https://www.linkedin.com/jobs/search?keywords=&location=United%20States"
            "&geoId=103644278&f_JT=F&f_E=2&f_PP=102571732"
        )
        print(f"📍 Using default URL")

    num = input("🔢 How many jobs to scrape? (default 10): ").strip()
    max_jobs = int(num) if num.isdigit() else 10

    total = scrape_linkedin_jobs(linkedin_url, max_jobs)

    if total > 0:
        print("\n" + "=" * 60)
        print(f"✅ Done! {total} jobs saved to {OUTPUT_FILE}")
        print("🎯 Run summarizer.py next")
        print("=" * 60)