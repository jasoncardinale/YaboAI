import http.client
import json


def chat_completion(prompt: str) -> str | None:
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
        print(f"Error: {response.status}")
        return None
