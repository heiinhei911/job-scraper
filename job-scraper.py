import pandas as pd
# import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
import time
import math
from pathlib import Path
from constants import *
from utils import export_utils, nlp_utils, webpage_utils
import globals

# Initialize variables
job = ""
job_error_ids = []
all_job_descriptions = []
all_job_org_keywords = []

options = Options()
options.add_argument("--headless=new")
# driver = webdriver.Chrome()
globals.driver = webdriver.Chrome(options=options)

while not job:
    # Prompt to ask for key word for searching (the job title)
    job = input("Type in the key word that you want to search for: ")
globals.job_combined = job.replace(" ", "-")
export_utils.update_folder_full_path()

# Create a "./jobs/" directory if not already exists and
Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)
# Create a "./jobs/{job listing folder}" directory
Path(globals.folder_full_path).mkdir(parents=True, exist_ok=True)
# Create blank csv file (and overwrite old one if already exists)
pd.DataFrame({}, columns=["Title", "Company", "Min. Years of Exp. Required", "Fresh Grad/Less Exp.", "Location", "Classification", "Salary", "Posted Date", "Job ID", "URL", "Frequent Words", "Job Description"]).to_csv(globals.csv_full_path, index=False, date_format="%Y%m%d %h%m")

search_extent = ""
total_jobs_count = webpage_utils.get_total_jobs_count()
max_page_count = math.ceil(int(total_jobs_count) / JOB_POSTINGS_PER_PAGE)
total_jobs_count_str = "\nThe total number of jobs found was: {0}\nType 'all' to search all jobs OR type in the number of page you want to search (MAX is {1}): ".format(total_jobs_count, str(max_page_count))

# Prompt to ask for the search extent
valid = False
while not valid:
    search_extent = input(total_jobs_count_str)

    if search_extent.isnumeric():
        if int(search_extent) > 0 and int(search_extent) <= max_page_count:
            valid = True
            search_extent = int(search_extent)
    elif search_extent.isalpha() and search_extent.lower() == "all":
        valid = True
        search_extent = max_page_count

# Initiate the scaping
for i in range(1, search_extent+1):
    print("Now Processing PAGE {0} / {1}".format(i, search_extent))
    job_listings_wrapper = webpage_utils.get_page_contents(cur_page = i)
    webpage_utils.retrieve_jobs(job_listings_wrapper, job_error_ids, all_job_descriptions, all_job_org_keywords)
    time.sleep(0.5)

# Get frequency count of the most frequently appeared ORG keywords
nlp_utils.count_org_words([kws for job_org_kws in all_job_org_keywords for kws in job_org_kws])
# Export the statistics related to the keywords of job listing
export_utils.export_stats(nlp_utils.get_most_frequent_words(all_job_descriptions))

print(f"\nDONE!! Output files saved to '{globals.folder_full_path}'" + (f"\n-- Error job IDs: {job_error_ids}" if len(job_error_ids) > 0 else ""))

# Quit BS driver
globals.driver.quit()