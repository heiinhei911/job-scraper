import pandas as pd
# import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from selenium.common.exceptions import TimeoutException
# from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup as bs
import time
from datetime import date
from dateparser import parse
import math
import re
from pathlib import Path

# Define global constants
BASE_URL = "https://hk.jobsdb.com"
OUTPUT_PATH = "./jobs/"
JOB_POSTINGS_PER_PAGE = 26

# Initialize variables
job = ""
job_combined = ""
job_ids = []
total_jobs_count = ""
last_avail_page = 0
csv_full_path = ""

driver = webdriver.Chrome()
page = None
html = None

def update_csv_full_path():
    # Update the name of the csv with the job title that the user has inputted,
    # as well as the full path of the csv to allow for saving later
    global csv_full_path
    csv_full_path = "{0}{1}_{2}.csv".format(OUTPUT_PATH, job_combined, date.today().strftime("%Y%m%d"))

    # Create a new csv with "-[number]" at the end if a file with the same name already exists
    i = 2
    while Path(csv_full_path).is_file():
        csv_full_path = "{0}{1}_{2}-{3}.csv".format(OUTPUT_PATH, job_combined, date.today().strftime("%Y%m%d"), i)
        i += 1

def load_DOM():
    # Initialize the DOM
    global html
    page = driver.page_source
    html = bs(page, "html.parser")

def get_page_contents(cur_page):
    # Retrieve the contents of the page that was returned from JobDB

    # Define the basic URL structure with pagination
    pagination = "?page=" + str(cur_page)
    url = BASE_URL + "/" + job_combined + "-jobs/full-time" + (pagination if cur_page > 1 else "")

    # Get HTML Content
    # page = requests.get(url)
    # html = list(soup.children)[2]
    driver.get(url)
    load_DOM()

    # Get job postings and their details
    search_results = html.select_one('div[data-automation="searchResults"]')
    split_view = list(search_results.select_one('div[data-automation="splitViewParentWrapper"] > div').children)
    # print(split_view)
    job_listings_wrapper = split_view[0]
    return job_listings_wrapper

def get_total_jobs_count():
    # Get total number of jobs found on the website
    job_count = get_page_contents(0).select_one('span[data-automation="totalJobsCount"]').get_text()
    return job_count.replace(",", "")

def retrieve_jobs(job_listings_wrapper):
    # Retrieve details of each individual job posting from the search results

    job_listings = []

    # Get indivdual job listings from its main divs
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-card-type="JobCard"]')))
    job_cards = job_listings_wrapper.select('article[data-card-type="JobCard"]')
    job_cards_click = driver.find_elements(By.CSS_SELECTOR, 'article[data-card-type="JobCard"]')

    for i, card in enumerate(job_cards_click):
        job_experience = None
        job_fresh_grad = False

        job_id = job_cards[i]["data-job-id"]

        # If current job ID can be found in the job_ids array, skip the current job
        # This way only UNIQUE jobs would be added into the job_listings array
        if job_id in job_ids:
            break

        # Proceed if job_id is unique
        card.find_element(By.CSS_SELECTOR, 'a[data-automation="jobTitle"]').click()
        try:
            # Since the element with the "jobAdDetails" tag is injected into the DOM using JavaScript,
            # we need to wait (5 secs) until that element is found before extracting details from it
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-automation="jobAdDetails"]')))
            load_DOM()
            requirements_list = [li.get_text() for li in html.select_one('div[data-automation="jobAdDetails"]').select("li")]
            for req in requirements_list:
                req_lowered = req.lower()
                if "year" in req_lowered:
                    years_of_exp_idx = re.search(r"\d", req)
                    job_experience = req[years_of_exp_idx.start()] if years_of_exp_idx is not None else None
                elif any(keyword in req_lowered for keyword in ["fresh", "less"]):
                    job_fresh_grad = True
        except Exception as e:
            # If the element with the "jobAdDetails" tag is not found in the DOM within 5 secs, throw an error
            print("ERROR: ", e)

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

        # Add the current job to job_listings array
        # Add the current job id to job_ids array
        job_listings.append(
            {
                "Title": job_title,
                "Company": job_company,
                "Min. Years of Exp. Required": job_experience,
                "Fresh Grad/Less Exp.": job_fresh_grad,
                "Location": ", ".join(job_location),
                "Classification": job_classification.replace("(", "").replace(")",""),
                "Salary": job_salary,
                "Posted Date": str(parse(job_listing_date)).split(":")[0] + ":00:00",
                "Job ID": job_id,
                "URL": "{0}/job/{1}".format(BASE_URL, job_id)
            }
        )
        job_ids.append(job_id)

    export_job_listings(job_listings)

def export_job_listings(job_listings):
    # Append the jobs in the job listings array into the csv
    df = pd.DataFrame(job_listings)
    df.to_csv(csv_full_path, mode="a", index=False, header=False)

while not job:
    # Prompt to ask for key word for searching (the job title)
    job = input("Type in the key word that you want to search for: ")
job_combined = job.replace(" ", "-")
update_csv_full_path()

# Create "./jobs/" directory if not already exists and
# Create blank csv file (and overwrite old one if already exists)
Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)
# Define column orders
pd.DataFrame({}, columns=["Title", "Company", "Min. Years of Exp. Required", "Fresh Grad/Less Exp.", "Location", "Classification", "Salary", "Posted Date", "Job ID", "URL"]).to_csv(csv_full_path, index=False, date_format="%Y%m%d %h%m")

search_extent = ""
total_jobs_count = get_total_jobs_count()
max_page_count = math.ceil(int(total_jobs_count) / JOB_POSTINGS_PER_PAGE)
total_jobs_count_str = "\nThe total number of jobs found was: {0}\nType 'all' to search all jobs OR type in the number of page you want to search (MAX is {1}): ".format(total_jobs_count, str(max_page_count))

# Prompt to ask for the search extent
search_extent = input(total_jobs_count_str)

try:
    # Validation for numeric input
    while int(search_extent) > max_page_count or int(search_extent) <= 0:
        search_extent = input(total_jobs_count_str)
    search_extent = int(search_extent)
except(ValueError):
    # Validation for "all"
    while search_extent.lower() != "all":
        search_extent = input(total_jobs_count_str)
    search_extent = max_page_count

for i in range(1, search_extent+1):
    # try:
        print("Now Processing PAGE {0} / {1}".format(i, search_extent))
        job_listings_wrapper = get_page_contents(cur_page = i)
        retrieve_jobs(job_listings_wrapper)
        time.sleep(0.5)
    # except Exception as e:
    #     print("ERROR at: ", i, e)
    #     break
print("\nDONE!! Output saved to '" + csv_full_path + "'" + ("\n--Cut short to page: " + str(last_avail_page) if last_avail_page > 0 else ""))
driver.quit()