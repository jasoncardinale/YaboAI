import os
import tempfile
import time

TEMP_DIR = tempfile.gettempdir()
PROMPT_FILE = os.path.join(TEMP_DIR, "yaboai_prompt.txt")
STATUS_FILE = os.path.join(TEMP_DIR, "yaboai_status.txt")

def generate_commentary(prompt: str):
    try:
        if os.path.exists(STATUS_FILE):
            os.remove(STATUS_FILE)

        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            f.write(prompt)

        # Wait for the status file to indicate success or failure
        timeout = 120  # Timeout in seconds
        start_time = time.time()

        while True:
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    status = f.read().strip()
                    if status == "true":
                        return True
                    elif status == "false":
                        return False
            except Exception:
                continue

            # Check for timeout
            if time.time() - start_time > timeout:
                return False

            # Sleep briefly to avoid busy-waiting
            time.sleep(0.1)
    except Exception:
        return False
    finally:
        if os.path.exists(STATUS_FILE):
            os.remove(STATUS_FILE)


# if __name__ == "__main__":
#     prompt = "The driver named Dabro has just set a personal best with a lap time of 1:33.456"

#     success = generate_commentary(prompt)

#     if success:
#         print("Audio played successfully.")
#     else:
#         print("Failed to process the prompt.")
    
