import pandas as pd
from pathlib import Path
from datetime import date
from constants import *
import globals

def update_folder_full_path():
    # Update the name of the csv with the job title that the user has inputted,
    # as well as the full path of the csv to allow for saving later
    globals.folder_full_path = "{0}{1}_{2}/".format(OUTPUT_PATH, globals.job_combined, date.today().strftime("%Y%m%d"))

    # Create a new folder with "-[number]" at the end if a file with the same name already exists
    i = 2
    while Path(globals.folder_full_path).is_dir():
        globals.folder_full_path = "{0}{1}_{2}-{3}/".format(OUTPUT_PATH, globals.job_combined, date.today().strftime("%Y%m%d"), i)
        i += 1

    globals.csv_full_path = globals.folder_full_path + "output.csv"
    globals.stats_full_path = globals.folder_full_path + "stats.xlsx"

def export_current_job_listings(job_listings):
    # Append the jobs in the job listings array into the csv
    df_listing = pd.DataFrame(job_listings)
    df_listing.to_csv(globals.csv_full_path, mode="a", index=False, header=False)

def export_stats(most_freq_common_words):
    # Export the most frequently appeared keywords and their counts into an Excel file
    columns = ["Keywords", "Frequency"]

    text_label_count_desc = dict(sorted(globals.text_label_count.items(), key=lambda item: item[1], reverse=True))
    df_freq_common_words = pd.DataFrame(most_freq_common_words.items(), columns=columns)
    df_freq_org_words = pd.DataFrame(text_label_count_desc.items(), columns=columns)
    with pd.ExcelWriter(globals.stats_full_path, engine = "openpyxl") as stats_writer:
        # df_stats = df_stats.rename(columns={df_stats.columns[0]: "Keywords", df_stats.columns[1]: "Frequency"})
        df_freq_common_words.to_excel(stats_writer, sheet_name="Common_Word_Freq", index=False)
        df_freq_org_words.to_excel(stats_writer, sheet_name="Org_Word_Freq", index=False)