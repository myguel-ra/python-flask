# Postmortem: Failing requests due to bad support dashboard deploy

## Summary

A large fraction of user requests timed out because a bad deploy of support dashboard spammed its backend with user search requests, which overwhelmed the primary DB cluster.

## Impact

About 20% of all requests failed for all users for 64 minutes from 15:11 to 16:15 due to accidental increased load from the support dashboard's user search endpoint. 

## Root causes

A refactor in the UI of the support dashboard introduced a bug in the debouncing code for keyboard input in the user search bar. This resulted in ~100x more user search requests to the backend. The SQL queries for user search take longer than typical production queries. Eventually most database connections were serving user search, starving out production traffic and causing a large fraction of requests to time out.


## Detection

On-call was paged when requests started timing out.


## Timeline

All times UTC on 2021-05-01.




| Time   | Event                                                                                                                                                                                                  |
|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 12:21  | dan merges #3821, introducing the bug in keyboard input debouncing                                                                                                                                     |
| 12:25  | #3821 makes it into production, but we don't see its effects immediately because the support dashboard is a single page application, and so it only manifests for support reps if they reload the page |
| ~13:30 | some initial chatter about support dashboard slowness in #support, but the common thread is unclear so it doesn't get escalated                                                                        |
| 15:00  | shift change in support, so new reps come online and start fetching the buggy code and begin issuing huge numbers of user search request                                                               |
| 15:11  | some requests begin timing out                                                                                                                                                                         |
| 15:16  | on-call (maimouna) is paged for request timeout                                                                                                                                                        |
| 15:19  | maimouna starts investigating                                                                                                                                                                          |
| 15:24  | maimouna narrows down timeouts to the database                                                                                                                                                         |
| 15:33  | maimouna looks into active database queries, sees a huge number of queries from user search and very few typical production queries                                                                    |
| 15:41  | on-call sees that there was a sharp increase in user search requests at around 15:00, and starts looking into deploys shortly before                                                                   |
| 15:54  | fatou happens to click through to the graph of user search queries, and notices that the count actually started to climb earlier                                                                       |
| 15:57  | maimouna switches from looking at recent deploys to looking at all deploys touching related code path                                                                                                  |
| 16:02  | maimouna finds #3821                                                                                                                                                                                   |
| 16:06  | maimouna merges #3833 reverting #3821                                                                                                                                                                  |
| 16:10  | #3833 makes it into production                                                                                                                                                                         |
| 16:12  | maimouna asks all support reps to refresh their dashboard                                                                                                                                              |
| 16:15  | database queries from user search start to drop                                                                                                                                                        |
| 16:17  | production traffic stops timing out                                                                                                                                                                    |



## What went well

Once we found #3821, we had everything back within ~15 minutes.


## What could have gone better

The bug was in production for almost two hours before we noticed it.

The support dashboard was degraded for some reps for about 1.5h before we started investigating.




## Where we got lucky

fatou popped in and noticed that the issue actually started earlier than 15:00. Without that we might have lost another 10+ minutes looking for the culprit deploy.

## Remediation items

- improve detection by adding client-side instrumentation in the support dashboard SPA
- add rate limiting to the API endpoints used by the support dashboard
- move database queries to a separate connection pool so that they don't starve production traffic
