import threading
def print_active_threads():

    # Get a list of all active threads
    active_threads = threading.enumerate()

    # Print the name of each active thread
    print("Active threads:")
    for thread in active_threads:
        print(f"- {thread.name}")

print_active_threads()