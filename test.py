import spacy
import pandas as pd

nlp = spacy.load('en_core_web_sm')

texts = ["""
    Python, sql, React, JavaScript, HTML, CSS, Tableau, Spacy, Selenium
"""]

for text in texts:
    doc = nlp(text)

    for entity in doc.ents:
        if entity.label_ == "ORG":
            print(entity.text, entity.label_)

# excel = pd.read_csv("./jobs/business-analyst_20240815/output.csv")
# print(list(excel["Frequent Words"]))