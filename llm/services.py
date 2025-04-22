import time


def chat_completion(prompt: str):
    try:
        # File paths for communication
        prompt_file = "prompt.txt"
        response_file = "response.txt"

        # Write the prompt to the file
        with open(prompt_file, "w") as f:
            f.write(prompt)

        # Wait for the response to be written by the external script
        timeout = 10  # Timeout in seconds
        start_time = time.time()

        while True:
            # Check if the response file exists
            try:
                with open(response_file, "r") as f:
                    response = f.read().strip()
                    if response:
                        # Delete the response file after reading
                        import os

                        os.remove(response_file)
                        return response
            except FileNotFoundError:
                pass

            # Check for timeout
            if time.time() - start_time > timeout:
                return "Error: Response timed out."

            # Sleep briefly to avoid busy-waiting
            time.sleep(0.1)

    except Exception as e:
        return "Error: {}".format(e)


# Call the main function
if __name__ == "__main__":
    # Example prompt to send to the external script
    prompt = "Tell me a joke about racing."

    # Call the chat_completion function
    response = chat_completion(prompt)

    # Print the response
    print("Response:", response)
