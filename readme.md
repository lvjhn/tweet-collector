# Node.js Collector Utility


### HOW TO USE 
1. Define your key search terms in the terms folder as a file e.g. `search_terms.txt`
2. Configure the `payload.json` file to use your search terms
    ```
    {
        "keys": {
            "consumer_key" : "ePMjAyl7gKO22sjpE2T0a0sjM",
            "consumer_secret" : "D54ABnb89peaG5I9ag68gFxrg8wPiDutg2TeXbyVr6NSpbY20z", 
            "access_token" : "1151896274821500928-VIqadoc3FaAHgpML3T5ersSMQifkHa", 
            "access_token_secret" : "rT32iUcI6umSYw3LCFuphjjvmzQ04Fquph7gLnuVjuGTN"
        }, 
        "search" : {
            "terms" : "terms/search_terms.txt",
            "pages" : 10, 
            "lang" : "tl",
            "result_type" : "recent", 
            "tweet_mode" : "extended", 
            "offset" : 0
        }
    }
    ```

1. Create a folder called `dropzone/`
2. Run `node searcher.js` to search for tweets in your search terms file.
3. Transfer the files folder in the dropzone to a folder `archives/`  
4. The tweets in the folders of the archive folder are going to be combined by the merger program
5. Created a folder called `datasets/` to hold the CSV datasets to be made by the merger program
6. Use `merger.py` to create a dataset out of the different files from the archive from both `Tagalog` and `English` filtered tweets. The files in the archives folder should follow this format `[Archive Name] ([Language])` e.g. `"Key Terms (English)"`
7. The step in #4 should create the following files. `with_duplicates.csv`, `no_duplicates.csv` and `deep_filtered.csv`. The file `no_duplicates.csv` contains tweets that don't consider the removal of usernames, hashtags and links in the filtering of tweets. The `deep_filtered.csv` file removes usernames, hashtags, links and extra whitespaces before filtering duplicates. 
8. Use `childgen.py` to generate child search terms from `deep_filtered.csv`

## Algorithm
### Definitions
1. `S` - array of search terms
2. `i` - pointer to the index of the current search term
3. `check_lim()` - checks the current rate limit
4. `search(metadata, cont` - searches an item
    * there are two modes for this function: 
      * `search()` or the initial mode searches the item without any previous state
      * `search(metadata, cont)` - continues searching an item based on a previous state
5. `trap()` - trap function for rate limits 
   * reexecutes the search function after 60 seconds if under rate limiting
6. `query(payload)` - calls the client to query a specific payload (low level)
    * returns three items 
      * `M` - metadata object
        * contains helpful information about the tweets
      * `N` - next page probability flag
        * set to `true` if the item is at `100` of `TMAX` (maximum number of tweets per request)
      * `T` - statuses array
        * list of statuses returned by the client given the payload
7. `s_pause(cb)` - pauses the execution for 60 seconds and then executes the callback `cb`, a wrapper function for `setTimeout()`
8. `do_cont(R)` - checks if the searching should continue for the current item (pages) depending on the results from the last query

## PSEUDOCODE
```bash
let S = ["a", "b", "c"]
let i = 0  # initial state

func search_item(metadata, next):
    item = S[i]
    trap(search_item, metadata, next)

    # first search 
    if metadata == null AND next == null: 
        payload = build_payload(item)
        R = query(payload)
        metadata = R.M 
        next = R.N
        statuses = R.S 
        save_results(R)

        # page searching
        if do_cont(R):
            s_pause(function() {
                search_item(metadata, next)
            })  # pause for 60 seconds
        else: 
            i = i + 1  # move to the next item
            search_item(null, null)

    else: 
        payload = build_next_page_payload(item, metadata)
        R = query(payload)
        metadata = R.M 
        next = R.N
        statuses = R.S 
        save_results(R)

        # page searching
        if do_cont(R):
            s_pause(function() {
                search_item(metadata, next)
            })  # pause for 60 seconds
        else: 
            i = i + 1  # move to the next item
            search_item(null, null)



func cl(): 
    # code to check rate limit

func build_payload(item):
    # code to build payload of item

func build_next_page_payload(item):
    # code to build payload of next item

func do_cont(R): 
    # code to determine whether to continue searching for the
    # next page based on the previous results

func s_pause(cb): 
    # code to pause the state for 60 secs and then execute a custom callback

func trap(cb, metadata, state):
    if cl() < 12: 
        # notifier if necessary
        sleep(60)
        cb(metadata, count)
    else:
        return

```
        