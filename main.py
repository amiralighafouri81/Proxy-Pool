import threading
import queue
import requests
from pymongo import MongoClient
from Proxy_Pool import Crawler
import time

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "ProxyPool"
COLLECTION_NAME = "ProxyLists"

# Proxy Websites
proxy_websites = [
    "https://www.sslproxies.org/",
    "https://free-proxy-list.net/",
    "https://www.us-proxy.org/",
    "https://www.proxy-list.download/HTTPS",
    "https://www.proxynova.com/proxy-server-list/"
]

# Thread-safe Queue for proxy validation
q = queue.Queue()

# Number of threads for validation
NUM_THREADS = 10

# Function to validate proxies
def validate_proxy(proxy):
    try:
        res = requests.get("http://ipinfo.io/json", proxies={"http": proxy, "https": proxy}, timeout=5)
        if res.status_code == 200:
            return True
    except:
        return False
    return False

# Worker function to validate proxies from the queue
def check_proxies(client, db):
    collection = db[COLLECTION_NAME]
    while True:
        proxy = q.get()
        if proxy is None:  # Exit signal
            break
        if validate_proxy(proxy):
            print(f"Valid proxy found: {proxy}")
            collection.update_one(
                {"proxy": proxy},
                {"$set": {"proxy": proxy, "valid": True}},
                upsert=True
            )
            print(f"{proxy} added to db")
        else:
            collection.delete_one({"proxy": proxy})
            print(f"Removed invalid proxy: {proxy}")
        q.task_done()

# Function to continuously crawl, validate, and update the MongoDB database
def update_proxies_in_db():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]

    while True:
        # Step 1: Crawl for new proxies
        crawler = Crawler(urls=proxy_websites)
        data = crawler.run()

        # Step 2: Add new proxies to the queue
        for page_data in data:
            for proxy in page_data["proxies"]:
                q.put(proxy)

        # Start threads for validation
        threads = []
        for _ in range(NUM_THREADS):
            t = threading.Thread(target=check_proxies, args=(client, db))
            t.start()
            threads.append(t)

        # Wait for all proxies to be checked
        q.join()

        # Ensure all threads terminate
        for _ in range(NUM_THREADS):
            q.put(None)
        for t in threads:
            t.join()

        # Sleep before the next round of crawling and validation
        print("-------------------------------------------\n"
              "-------------------------------------------\n"
              "-------------------------------------------")
        print("wait for update")
        print("-------------------------------------------\n"
              "-------------------------------------------\n"
              "-------------------------------------------")
        time.sleep(20)  # Wait before updating again

# Start the proxy updater
update_proxies_in_db()
