import time
import os
import ollama

# File paths
PROMPT_FILE = "prompt.txt"
RESPONSE_FILE = "response.txt"


def process_prompt():
    """
    Reads the prompt from the prompt file, sends it to Ollama, and writes the response to the response file.
    """
    try:
        # Check if the prompt file exists
        if not os.path.exists(PROMPT_FILE):
            return

        # Read the prompt from the file
        with open(PROMPT_FILE, "r") as f:
            prompt = f.read().strip()

        if not prompt:
            return

        print(f"Processing prompt: {prompt}")

        # Send the prompt to Ollama
        response = ollama.generate(model="gemma3:4b", prompt=prompt)

        # Extract the response text
        response_text = response["response"].strip()

        # Write the response to the response file
        with open(RESPONSE_FILE, "w") as f:
            f.write(response_text)

        print(f"Response written to {RESPONSE_FILE}: {response_text}")

        # Clear the prompt file after processing
        os.remove(PROMPT_FILE)

    except Exception as e:
        print(f"Error processing prompt: {e}")


def main():
    """
    Continuously monitors the prompt file for new prompts and processes them.
    """
    print("Starting Ollama file processor...")
    while True:
        process_prompt()
        time.sleep(0.5)  # Check for new prompts every 500ms


if __name__ == "__main__":
    main()
