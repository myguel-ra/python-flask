import os
RATELIMIT_URL = 'http://' + os.environ.get('ENVOY_RATELIMIT_SERVICE_HOST') + ':8080/json'
# RATELIMIT_URL = 'http://localhost:8080/json'
# ENVOY_RATELIMIT_SERVICE_PORT

RATELIMIT_REQUEST = {
  "domain": "support-dashboard",
  "descriptors": [
    {
      "entries": [
        {
          "key": "endpoint",
          "value": ""
        }
      ]
    },
    {
      "entries": [
        {
          "key": "endpoint",
          "value": ""
        },
        {
          "key": "user",
          "value": ""
        }
      ]
    }
  ]
}
