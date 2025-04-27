import time

def run_service():
    print("Service started")
    while True:
        time.sleep(1)
        print("Service running")

if __name__ == "__main__":
    run_service()