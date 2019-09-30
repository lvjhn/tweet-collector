let fs = require('fs')
let Twit = require('twit')


class Searcher {
    constructor(payload_file) {
        /** Initialize Payload File */
        this.payload_file = payload_file
        this.payload = this.load_payload()
        /** Initialize API Client */
        this.client = this.load_client()
        this.S = this.load_search_terms()
        this.i = 0
        this.pager = 0
        console.log(this.S)
    }
    

    load_payload() {
        let payload_file = this.payload_file
        let payload_str = 
            fs.readFileSync(payload_file)
        payload_str = 
            payload_str.toString() 
        let payload = 
            JSON.parse(payload_str)
        return payload
    }

    load_client() {
        let payload = this.payload
        this.client = new Twit(payload.keys)
        return this.client
    }

    load_search_terms() {
        let terms_file = this.payload.search.terms 
        let terms = fs.readFileSync(terms_file).toString() 
        terms = terms.split("\n")
        return terms
    }

    /** Wrapper Functions for Synchronous API Calls */

    // function to get the remaining API calls for the current window's 
    // /search/tweets endpoint
    check_lim() {
        let self = this
        return new Promise((resolve, reject) => {
            try {
                let endpoint = "/application/rate_limit_status"
                self.client.get(endpoint, (err, data) => {
                    if(err) 
                        resolve(0)
                    else {
                        let resources = data["resources"]
                        let limit = resources["search"]["/search/tweets"]
                        limit = limit.remaining
                        resolve(limit)
                    }
                })
            } catch(e) {
                resolve(0)
            }
        }) 
    }

    // function to query a specific item from twitter given a payload object
    query(payload, verbose) {
        if(!verbose) 
            verbose = false
        let self = this 
        return new Promise((resolve, reject) => {
            let endpoint = "/search/tweets"
            self.client.get(endpoint, payload, (err, data) => {
                if(err)
                    reject(err)
                else {
                    if(verbose) {
                        console.log("Querying for payload: ")
                        console.log(payload)
                    }
                    let M = data.search_metadata
                    let S = data.statuses 
                    let N = (S.length == 100)
                    if(verbose) {
                        console.log("Query Results:")
                        console.log("Number of Tweets: " + S.length)
                    }
                    resolve({
                        statuses: S,
                        metadata: M,
                        next: N
                    })
                }
            })
        })
    }


    /** Helper Functions for the Search Roll */

    // builds payload on initial state (no max id)
    build_payload(item) {
        let self = this
        let search = self.payload.search
        return {
            q: item, 
            lang: search.lang, 
            count: 100, 
            results_type: "recent",
            tweet_mode: "extended"
        }
    }

    // builds payload on next page state 
    build_next_results_payload(item, metadata) {
        let self = this
        // convert next result string to object
        let next_page = self.querys_to_url(metadata.next_results)
        // merge payload details 
        let payload = self.build_payload(item)
        for(var key in next_page) {
            payload[key] = next_page[key]
        }
        return payload
    }

    // converts a query string to an object
    querys_to_url(querys) {
        // remove first letter
        let qs = querys.substring(1, querys.length)
        // split by ampersand & 
        qs = qs.split("&")
        // split each item in qs by =  and 
        // add each keyval pair to map 
        let map = {} 
        for(var i in qs) {
            let entry = qs[i]
            let vals = entry.split("=")
            let key = vals[0]
            let val = vals[1]
            map[key] = val
        }
        return map
    }

    // code to determine whether to continue searching for the next
    // page based on the previous results 
    do_cont(R) {
        let self = this 
        let maxpage = self.payload.search.pages
        // if pager does not reach maxpage yet
        // and if R.next is true
        if(self.pager < maxpage && R.next) {
            return true
        } else {
            return false
        }
    }

    // helper function to save the results to the dropzone as a single 
    // file 
    save_results(item, R) {
        let self = this
        let json_str = JSON.stringify(R)
        fs.writeFileSync("dropzone/" + item.q + "." + self.pager + "." + item.lang + ".json", json_str, ()=>{})
        fs.appendFileSync(".failsafe", (new Date().toString()) + " " + item.q + " : " + self.pager + "\n")
    }

    // helper function to load a specific result as a checkpoint for the next
    // result 
    async load_results_as_checkpoint(results_file) {
        // code to return the R, S, N values in the results file [TODO]
        let self = this
        let chunks = results_file.split("/")[1]
        let index = self.S.indexOf(chunks.split(".")[0])
        self.i = index 
        self.pager = chunks.split(".")[1]
        // load the file 
        let checkpoint_file = fs.readFileSync(results_file).toString() 
        let checkpoint = JSON.parse(checkpoint_file)
        await self.search_item(checkpoint.metadata, checkpoint.next)
    } 

    // trap function (checks the current limit, if under rate limiting,
    // waits for 60 seconds and then reexecutes the search_item() function) 
    trap(search_item, metadata, next) {
        let self = this 
        return new Promise(async (resolve, reject) => {
            let lim = await self.check_lim()
            console.log("> In trap() : Rate limit check result: " + lim)
            if(lim < 12) {
                let time = 0
                let reset = 60
                let speed = 1000
                let t = setInterval(() => {
                    let downtime = (reset - time)
                    if(downtime <= 0) {
                        clearInterval(t)
                        return
                    } else {
                        console.log("Rate limit exceeded, checking again in " + downtime) 
                        time++
                    }
                }, speed)
                console.log("Creating timeout function...")
                // notifier if necessary 
                setTimeout(async () => {
                    let si = search_item 
                    let m = metadata 
                    let n = next
                    await self.search_item(si, m, n)
                    resolve(lim)
                }, reset * speed)
                console.log("Created timeout function..")
            } else {
                resolve(lim)
            }
        })
    }
    
    // search pause function, a mod of the trap funciton
    // to pause the search state in between pages
    async s_pause() {
        return new Promise(async (resolve, reject) => {
            let time = 0
                let reset = 60
                let speed = 1000
                let t = setInterval(() => {
                    let downtime = (reset - time)
                    if(downtime <= 0) {
                        clearInterval(t)
                        return
                    } else {
                        console.log("To query next page, quering again in " + downtime) 
                        time++
                    }
                }, speed)
                console.log("Creating timeout function...")
                // notifier if necessary 
                setTimeout(async () => {
                    resolve(true)
                }, reset * speed)
                console.log("Created timeout function..")
        })
    }


    /** ROLLING SEARCH FUNCTION */
    async search_item(metadata, next) {
        let self = this
        
        // get the current item from the search terms array
        let item = self.S[self.i]
        console.log("Item " + (self.i + 1) + " of " + self.S.length)
        if(!metadata)
            metadata = null 
        if(!next)
            next = null 

        console.log("Checking rate limits...")
        // execute the trap function to be safe 
        let trap = await self.trap(this.search_item, metadata, next)

        console.log("Rate limit on checking: " + trap)
        console.log("Rate limit check passed...")

        if(metadata == null || next == null) {
            console.log("Initial search state.")
            self.pager = 0
            console.log("PAGE " + (self.pager + 1) + " OF 3 OF " + item)
            console.log("Building payload...")
            let payload = self.build_payload(item)
            console.log("Querying item")
            let R = await self.query(payload)
            let metadata = R.metadata 
            let next = R.next
            let statuses = R.statuses 
            metadata.statuses_count = statuses.length
            console.log("Saving results")
            self.save_results(payload, R)

            // next page searching 
            if(self.do_cont(R)) {
                console.log("Next page searching.")
                self.pager += 1
                this.search_item(metadata, next)
            } else {
                self.i = self.i + 1
                console.log("Next item searching.")
                this.search_item()
            }
        } else {
            console.log("Next page search state.")
            let payload = self.build_next_results_payload(item, metadata)
            let R = await self.query(payload)
            metadata = R.metadata 
            next = R.next
            let statuses = R.statuses 
            self.save_results(payload, R)

            // next page searching 
            if(self.do_cont(R)) {
                console.log("Next page searching.")
                self.pager += 1
                this.search_item(metadata, next)
            } else {
                self.i = self.i + 1
                console.log("Next item searching.")
                this.search_item()
            }
        }



    }

    /** Executes an asynchronous callback based on the context **/
    execute(cb) {
        let self = this
        let cbv = cb(self)
    }
}

let searcher = new Searcher("payload.json")

searcher.execute(async (self) => {
    let payload = {
        q: "item"
    }

    let metadata = {
        completed_in: 0.049,
        max_id: 1178320397915213800,
        max_id_str: '1178320397915213824',
        next_results: '?max_id=1178320375802761215&q=item&include_entities=1',
        query: 'item',
        refresh_url: '?since_id=1178320397915213824&q=item&include_entities=1',
        count: 15,
        since_id: 0,
        since_id_str: '0'
    }
    
    // console.log(await self.query(payload, true))
    // console.log(self.build_next_results_payload("item", metadata))
    // await searcher.search_item()

    await searcher.load_results_as_checkpoint("dropzone/technology.3.tl.json")
})

