import json 
import os
import pprint as pp

def ls_folders(path): 
    return list(os.walk(path))[0][1]

def ls_files(path):
    return list(os.walk(path))[0][2]

def list_datafiles(dataset): 
    return ls_files("archives/" + dataset)

def list_datasets():
    return ls_folders("archives/")

def list_topics(dataset): 
    files = list_datafiles(dataset) 
    topics = {}
    i = 0
    for file in files:
        chunks = file.split(".") 

        topic = chunks[0]
        
        page = chunks[1]
        lang = chunks[2]
        
        topic_name = topic
        if topic_name not in topics: 
            topics[topic_name] = 1
        else: 
            topics[topic_name] += 1
        i += 1
    return topics

# function to load a specific topic from a dataset into memory, returns 
# an array that contains all of the tweets in all of the pages
def load_topic(dataset, topic, npages): 
    file_prefix = "archives/" + dataset + "/" + topic 
    pages = [] 

    # identify language from dataset name 
    chunks = dataset.split(" ")
    language = chunks[-1]
    language = language[1:-1]

    # convert the full language name to its language code
    lang = None 
    if language == "Tagalog": 
        lang = "tl"
    else: 
        lang = "en"
    
    # populates the pages array with the current information
    for page_no in range(npages): 
        file = f"{file_prefix}.{page_no}.{lang}.json"
        pages.append(file)

    # placeholder for the merged tweets
    tweets = []

    # load each file in the array 
    for file in pages: 
        if os.path.exists(file):
            # open the datafile 
            file_content = open(file).read() 
            # parse the file content as json 
            file_data = json.loads(file_content)
            # add a special tag to all of the tweets
            # in this current file about the current topic 
            statuses = file_data["statuses"]
            for status in statuses: 
                status["search_term"] = topic
                status["language"] = language
                status["dataset"] = dataset
            tweets += statuses

    return tweets

# function to load all of the files in a dataset given a 
# topic listing, returns an array of all the merged
# tweets
def load_dataset(dataset): 
    topics = list_topics(dataset)
    dataset_tweets = []

    # for each topic in the topic listing 
    for topic in topics: 
        pages = topics[topic]
        # use the load_topic function to load the current
        # datafile referred to by this current entry
        topic_tweets = load_topic(dataset, topic, pages)
        dataset_tweets += topic_tweets 

    return dataset_tweets

# loads all tweets from all datasets 
def load_all(): 
    datasets = list_datasets() 
    all_tweets = []
    for dataset in datasets: 
        print("Loading dataset `" + dataset + "`")
        tweets = load_dataset(dataset)
        print("Loaded " + str(len(tweets)) + " tweets")
        all_tweets += tweets 
    return all_tweets

# filter tweet data 
# - returns the most relevant data from a tweet 
# - id, author, full_text (not truncated),
# - created_at, language, search_term
def filter_tweet_data(tweet): 
    id = tweet["id_str"]
    author = tweet["user"]["screen_name"]
    
    # for the full text we're going to check first
    # if the tweet has a retweeted_status field 
    text = "" 
    if "retweeted_status" in tweet:
        text = tweet["retweeted_status"]["full_text"].strip()
    else: 
        text = tweet["full_text"].strip()

    created_at = tweet["created_at"].strip()
    language = tweet["language"].strip()
    search_term = tweet["search_term"].strip()
    dataset = tweet["dataset"].strip()

    return {
        "id" : id, 
        "author" : author, 
        "text" : text, 
        "created_at" : created_at, 
        "language" : language, 
        "search_term" : search_term, 
        "dataset_domain" : dataset
    }

# ---------- DRIVER PROCEDURES --------------#

import pandas as pd
all_tweets = load_all()
filtered_tweets = [filter_tweet_data(tweet) for tweet in all_tweets]
filtered_tweets = pd.DataFrame(filtered_tweets)


print("Before removal of duplicates: " + str(len(filtered_tweets)) + " tweets")
filtered_tweets.to_csv("datasets/with_duplicates.csv")
refiltered_tweets = filtered_tweets.drop_duplicates(subset=["text"])
print("After removal of duplicates: " + str(len(filtered_tweets)) + " tweets")
refiltered_tweets.to_csv("datasets/no_duplicates.csv")

import re
# remove usernames and see if something changes
texts = {}
deep_filtered = pd.DataFrame(columns=refiltered_tweets.columns)
duplicates = 0

for index, row in refiltered_tweets.iterrows(): 
    # remove usernames and lowercase
    no_un = re.sub("@[^\s]+", "", row["text"])
    no_un = re.sub(r"http\S+", "", no_un)
    no_un = no_un.lower()
    if no_un not in texts:
        texts[no_un] = 1
        deep_filtered.loc[index] = row
    else: 
        print("Duplicate removed.")
        duplicates += 1

    print("(" + str(index/len(refiltered_tweets)*1000//10) +  "%) Processing " + str(index) + " of " + str(len(refiltered_tweets)) + " | Duplicates removed: " + str(duplicates) + " | Running size: " + str(len(deep_filtered)))

print("Deep duplicate removal: " + str(len(deep_filtered)) + " tweets")
deep_filtered.to_csv("datasets/deep_filtered.csv")
