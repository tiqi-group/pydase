# RESTful API

The `pydase` RESTful API allows for standard HTTP-based interactions and provides access to various functionalities through specific routes. This is particularly useful for integrating `pydase` services with other applications or for scripting and automation.

For example, you can get a value like this:

```python
import json

import requests

response = requests.get(
    "http://<hostname>:<port>/api/v1/get_value?access_path=<full_access_path>"
)
serialized_value = json.loads(response.text)
```

To help developers understand and utilize the API, we provide an OpenAPI specification. This specification describes the available endpoints and corresponding request/response formats.

## OpenAPI Specification

<swagger-ui src="./openapi.yaml"/>
