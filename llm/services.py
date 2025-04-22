import http.client
import json

import ac  # type: ignore


def chat_completion(prompt: str):
    conn = http.client.HTTPConnection("localhost", 11434)
    headers = {"Content-type": "application/json"}
    payload = json.dumps(
        {
            "model": "gemma3:4b",
            "prompt": prompt,
            "stream": False,
        }
    )

    conn.request("POST", "/api/generate", payload, headers)
    response = conn.getresponse()

    if response.status == 200:
        response_data = response.read().decode()
        return json.loads(response_data)["response"].strip()
    else:
        ac.console("Error: {}".format(response.status))
        return None
