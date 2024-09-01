from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup as bs
import re
from dateparser import parse
from constants import *
import globals
from utils import export_utils, nlp_utils

def load_DOM():
    # Initialize the DOM
    page = globals.driver.page_source
    globals.html = bs(page, "html.parser")

def get_page_contents(cur_page):
    # Retrieve the contents of the page that was returned from JobDB

    # Define the basic URL structure with pagination
    pagination = "?page=" + str(cur_page)
    url = BASE_URL + "/" + globals.job_combined + "-jobs/full-time" + (pagination if cur_page > 1 else "")

    # Get HTML Content
    # page = requests.get(url)
    # html = list(soup.children)[2]
    globals.driver.get(url)
    load_DOM()

    # Get job postings and their details
    search_results = globals.html.select_one('div[data-automation="searchResults"]')
    split_view = list(search_results.select_one('div[data-automation="splitViewParentWrapper"] > div').children)
    job_listings_wrapper = split_view[0]
    return job_listings_wrapper

def get_total_jobs_count():
    # Get total number of jobs found on the website
    job_count = get_page_contents(0).select_one('span[data-automation="totalJobsCount"]').get_text()
    return job_count.replace(",", "")

def retrieve_jobs(job_listings_wrapper, job_error_ids, all_job_descriptions, all_job_org_keywords):
    # Retrieve details of each individual job posting from the search results

    job_listings = []
    job_ids = []

    # Get indivdual job listings from its main divs
    WebDriverWait(globals.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-card-type="JobCard"]')))
    job_cards = job_listings_wrapper.select('article[data-card-type="JobCard"]')
    job_cards_click = globals.driver.find_elements(By.CSS_SELECTOR, 'article[data-card-type="JobCard"]')

    for i, card in enumerate(job_cards_click):
        job_experience = None
        job_fresh_grad = False

        job_id = job_cards[i]["data-job-id"]

        # If current job ID can be found in the job_ids array, skip the current job
        # This way only UNIQUE jobs would be added into the job_listings array
        if job_id in job_ids:
            continue

        # Proceed if job_id is unique
        card.find_element(By.CSS_SELECTOR, 'a[data-automation="jobTitle"]').click()
        # Since the element with the "jobAdDetails" tag is injected into the DOM using JavaScript,
        # we need to wait (5 secs) until that element is found before extracting details from it
        try:
            WebDriverWait(globals.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-automation="jobAdDetails"]')))
        except TimeoutException:
            try:
                WebDriverWait(globals.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'section[data-automation="JDVExpired"]')))

                print(f"-- Expired job ID: {job_id}")
                job_error_ids.append(int(job_id))
            finally:
                continue

        load_DOM()
        # requirements_list = [li.get_text() for li in html.select_one('div[data-automation="jobAdDetails"]').select("li")]
        job_description = globals.html.select_one('div[data-automation="jobAdDetails"]').get_text()
        all_job_descriptions.append(job_description)
        # print(requirements_list)
        job_description_lowered = job_description.lower()
        # if "year" in job_description_lowered:
        years_of_exp_idx = re.search(r"(\b\d+).{0,50}(?=year).{0,100}(?=experience)", job_description_lowered)
        # print(years_of_exp_idx)
        job_experience = years_of_exp_idx.group(1) if years_of_exp_idx is not None else None
        # print(job_experience)
        if any(keyword in job_description_lowered for keyword in ["fresh ", "less experience"]):
            job_fresh_grad = True

        # Extract job details from their respective locations
        job_card_details = list(job_cards[i].children)[-1]
        job_company_tag = job_card_details.select_one('a[data-automation="jobCompany"]')
        job_salary_tag = job_card_details.select_one('span[data-automation="jobSalary"] > span')
        job_title = job_card_details.select_one('a[data-automation="jobTitle"]').get_text()
        job_location = [location_description.get_text() for location_description in job_card_details.select('a[data-automation="jobLocation"]')]
        job_salary = job_salary_tag.get_text().replace("–", "-") if job_salary_tag is not None else ""
        job_classification = job_card_details.select_one('a[data-automation="jobClassification"]').get_text()
        job_listing_date = job_card_details.select_one('span[data-automation="jobListingDate"]').get_text()
        job_company = job_company_tag.get_text() if job_company_tag is not None else "**Private"
        job_freq_org_keywords = nlp_utils.get_org_words(job_description)
        all_job_org_keywords.append(job_freq_org_keywords)

        # Define job_listing_obj and add the current job obj to job_listings array
        job_listing_obj = {
                "Title": job_title,
                "Company": job_company,
                "Min. Years of Exp. Required": job_experience,
                "Fresh Grad/Less Exp.": job_fresh_grad,
                "Location": ", ".join(job_location),
                "Classification": job_classification.replace("(", "").replace(")",""),
                "Salary": job_salary,
                "Posted Date": str(parse(job_listing_date)).split(" ")[0],
                "Job ID": job_id,
                "URL": "{0}/job/{1}".format(BASE_URL, job_id),
                "Frequent Words": job_freq_org_keywords,
                "Job Description": job_description
            }
        job_listings.append(job_listing_obj)
        # Add the current job id to job_ids array
        job_ids.append(job_id)

    export_utils.export_current_job_listings(job_listings)
