import os
RATELIMIT_URL = os.environ.get('ENVOY_RATELIMIT_SERVICE_HOST')
RATELIMIT_PORT = os.environ.get('ENVOY_RATELIMIT_SERVICE_PORT')


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
