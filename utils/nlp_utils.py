import numpy as np
import spacy
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction._stop_words import ENGLISH_STOP_WORDS
import globals

nlp = spacy.load("en_core_web_sm")

def get_org_words(req):
    # Get a list of ORG words using Spacy NLP
    req_analyzed = nlp(req)
    return [entity.text for entity in req_analyzed.ents if entity.label_ == "ORG"]

def count_org_words(org_list):
    # Get the count of ORG keywords and output a {keyword: count} dict of all the keywords
    for org_word in org_list:
        if org_word not in globals.text_label_count.keys():
            globals.text_label_count[org_word] = 1
        else:
            globals.text_label_count[org_word] += 1

def get_most_frequent_words(req, length=50):
    # Return a dict of the most frequent words of a job description input with custom length input
    vect = CountVectorizer(max_df=0.70, stop_words=list(ENGLISH_STOP_WORDS))
    vect_fit = vect.fit_transform(req)
    # return vect.get_feature_names_out()
    # return dict(zip(vect.get_feature_names_out(), vect_fit.toarray().sum(axis=0)))
    word_count_dict = dict(zip(vect.get_feature_names_out(), [int(sum) for sum in np.asarray(vect_fit.sum(axis=0))[0]]))
    word_count_dict_desc = dict(sorted(word_count_dict.items(), key=lambda item: item[1], reverse=True))
    return dict(list(word_count_dict_desc.items())[0:length])
