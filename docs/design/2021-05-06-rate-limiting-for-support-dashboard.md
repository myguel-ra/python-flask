# Design: Rate limiting for support dashboard API

## Summary

Add a rate limiting service that we will initially use to rate limit requests from the support dashboard.

## Motivation

We [recently had an outage][postmortem] where a large number of support dashboard requests crowded out production traffic. We want to prevent non-core traffic like the support dashboard from impacting the end user experience.

[postmortem]: ../postmortems/2021-05-01-failing-requests-due-to-bad-support-dashboard-deploy.md


## Design

We'll use [Envoy's ratelimit service][ratelimit] with redis as a backend. It's a generic rate limiting service that can be set up to apply several rate limits at once. For our specific use case, we want to limit support dashboard requests in two ways:
- limit each support rep to 3 customer search requests per minute
- limit the total number of customer search requests across all support reps to 20 per minute

The first limit protects against a single user's support dashboard frontend from making too many requests. The second limit ensures that—in aggregate—the load from support customer search doesn't get so high as to risk impacting customer traffic.

ratelimit provides an [HTTP interface][http] at `/json` that can be queried to see if a request would exceed any rate limits.

[ratelimit]: https://github.com/envoyproxy/ratelimit/
[http]: https://github.com/envoyproxy/ratelimit/#http-port

### Config
<a name="config"></a>

This ratelimit config implements our the two-level rate limit described above:

```yaml
domain: support-dashboard
descriptors:
  - key: endpoint
    value: /customers/search
    rate_limit:
      unit: minute
      requests_per_unit: 20
    descriptors:
    - key: user
      rate_limit:
        unit: minute
        requests_per_unit: 3
```

### Example HTTP request

To get the desired behaviour, we make a POST request with two descriptors: one for the global customer search rate limit, and another for the per-user rate limit.

```json
{
  "domain": "support-dashboard",
  "descriptors": [
    {
      "entries": [
        {
          "key": "endpoint",
          "value": "/customers/search"
        }
      ]
    },
    {
      "entries": [
        {
          "key": "endpoint",
          "value": "/customers/search"
        },
        {
          "key": "user",
          "value": "papa.sarr@wave.com"
        }
      ]
    }
  ]
}

```

The response status will either be _200 OK_ or _429 Too Many Requests_. The response body will be JSON with an `overallCode` field whose value is either `OK` or `OVER_LIMIT`. It also includes information about the limit for each descriptor in the request. For example, this response indicates that the request was rate limited because the global rate limit was hit, even though this particular user's limit was not:

```json
{
  "overallCode": "OVER_LIMIT",
  "statuses": [
    {
      "code": "OVER_LIMIT",
      "currentLimit": {
        "requestsPerUnit": 20,
        "unit": "MINUTE"
      },
      "durationUntilReset": "13s"
    },
    {
      "code": "OK",
      "currentLimit": {
        "requestsPerUnit": 3,
        "unit": "MINUTE"
      },
      "durationUntilReset": "13s",
      "limitRemaining": 2
    }
  ]
}
```


### Rate limiting as middleware
<a name="middleware"></a>

The most straightforward way to add rate limiting to the customer search endpoint would be to add a request to the ratelimit service directly in the function that handles customer search. But this means any time we want to add a ratelimit to another endpoint, we'd have to modify the API backend code.

Instead, we can add a middleware that checks the rate limit for the request's user and endpoint. This way additional rate limits can be added purely by modifying the ratelimit service's configuration.

For example, we would be able to add rate limiting to the `/transactions/search` endpoint by making this change to the config:

```diff
--- before
+++ after
@@ -3,10 +3,15 @@
   - key: endpoint
     value: /customers/search
     rate_limit:
       unit: minute
       requests_per_unit: 20
     descriptors:
     - key: user
       rate_limit:
	unit: minute
	requests_per_unit: 3
+  - key: endpoint
+    value: /transactions/search
+    rate_limit:
+      unit: minute
+      requests_per_unit: 10
```


## Execution
<a name="execution"></a>

Suggested order for implementation:

1. deploy redis
2. deploy the rate limiter service with the [config defined above](#config)
3. modify the search_customers handler to make a request to the ratelimit service for each request, and return a _429 Too Many Requests_ status code if the request is over limit
4. move the ratelimit check into a middleware or `before_request` callback [as described above](#middleware)
5. add a rate limit to the `/transactions/search` endpoint by changing the configuration of the ratelimit service

### Custom ratelimit image

There's a custom container image for ratelimit: europe-west1-docker.pkg.dev/wavemm-sre-takehome-miguel/containers/ratelimit

This has a few quality-of-life improvements over the one that the Envoy project provides:
- it sets an entrypoint so that you don't need to specify a command
- it reads its configuration from `/etc/ratelimit/config/config.yaml`
- it logs at debug level
- the only environment variable needed is `REDIS_URL`


## Open questions

### Should we put redis in the kubernetes cluster or use [GCP's MemoryStore][memorystore-redis]?

Since the data we're storing is really transient, we can just go with whichever is easier to deploy.

[memorystore-redis]: https://cloud.google.com/memorystore/docs/redis
