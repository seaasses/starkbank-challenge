import threading
from src.config.settings import NUM_CONSUMERS_PER_INSTANCE
from src.services.queue_service import start_consumer


if __name__ == "__main__":
    print(f"Starting {NUM_CONSUMERS_PER_INSTANCE} consumers...", flush=True)

    # Create consumer threads
    threads = []
    for i in range(NUM_CONSUMERS_PER_INSTANCE):
        thread = threading.Thread(target=start_consumer, args=("task_queue",))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        print(f"Started consumer thread {i+1}", flush=True)

    # Wait for all threads
    for thread in threads:
        thread.join()
