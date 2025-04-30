import os
import time


def chat_completion(prompt: str):
    try:
        # File paths for communication
        prompt_file = "prompt.txt"
        status_file = "status.txt"

        # Write the prompt to the file with utf-8 encoding
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        # Wait for the status file to indicate success or failure
        timeout = 20  # Timeout in seconds
        start_time = time.time()

        while True:
            # Check if the status file exists
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    status = f.read().strip()
                    if status == "true":
                        os.remove(status_file)
                        return True
                    elif status == "false":
                        os.remove(status_file)
                        return False
            except FileNotFoundError:
                pass

            # Check for timeout
            if time.time() - start_time > timeout:
                return False

            # Sleep briefly to avoid busy-waiting
            time.sleep(0.1)

    except Exception as e:
        print(f"Error: {e}")
        return False


# Call the main function
if __name__ == "__main__":
    # Example prompt to send to the external script
    prompt = "Tell me a joke about racing."

    # Call the chat_completion function
    success = chat_completion(prompt)

    # Print the result
    if success:
        print("Audio played successfully.")
    else:
        print("Failed to process the prompt.")
