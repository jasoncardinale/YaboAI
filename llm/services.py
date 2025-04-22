import socket
import json


def chat_completion(prompt: str):
    try:
        # Connect to the server
        host = "localhost"
        port = 11434
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        # Create the HTTP request payload
        payload = (
            "POST /api/generate HTTP/1.1\r\n"
            "Host: localhost\r\n"
            "Content-Type: application/json\r\n"
            "Content-Length: {}\r\n"
            "\r\n"
            "{}"
        )
        body = '{"model": "gemma3:4b", "prompt": "%s", "stream": false}' % prompt
        request = payload.format(len(body), body)

        # Send the HTTP request
        sock.sendall(request.encode("utf-8"))

        # Receive the response headers
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

        # Split headers and body
        header_data, _, body_data = response.partition(b"\r\n\r\n")

        # Parse the headers
        headers = header_data.decode("utf-8").split("\r\n")
        content_length = 0
        for header in headers:
            if header.lower().startswith("content-length:"):
                content_length = int(header.split(":")[1].strip())
                break

        # Receive the rest of the body if needed
        while len(body_data) < content_length:
            chunk = sock.recv(4096)
            if not chunk:
                break
            body_data += chunk

        # Close the socket
        sock.close()

        # Parse the response body
        response_str = body_data.decode("utf-8")
        return json.loads(response_str)["response"].strip()

    except Exception:
        # ac.console("Error: {}".format(e))
        return None


# Call the main function
if __name__ == "__main__":
    # Example prompt to send to the server
    prompt = "Tell me a joke about racing."

    # Log the prompt being sent
    # ac.console("Testing chat_completion with prompt: '{}'".format(prompt))

    # Call the chat_completion function
    response = chat_completion(prompt)

    # Log the response
    if response:
        print(response)
    else:
        print("No response or an error occurred.")
