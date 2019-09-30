# Node.js Collector Utility

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
        