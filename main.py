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

# List to store valid proxies
valid_proxies = []

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
def check_proxies():
    global q, valid_proxies
    while True:
        proxy = q.get()
        if proxy is None:  # Exit signal
            break
        if validate_proxy(proxy):
            print(f"Valid proxy found: {proxy}")
            valid_proxies.append(proxy)
        q.task_done()

# Function to continuously crawl, validate, and update the MongoDB database
def update_proxies_in_db():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    while True:
        # Step 1: Crawl for new proxies
        crawler = Crawler(urls=proxy_websites)
        data = crawler.run()

        # Step 2: Validate crawled proxies
        new_proxies = []
        for page_data in data:
            for proxy in page_data["proxies"]:
                q.put(proxy)
                new_proxies.append(proxy)

        # Start threads for validation
        threads = []
        for _ in range(NUM_THREADS):
            t = threading.Thread(target=check_proxies)
            t.start()
            threads.append(t)

        # Wait for all proxies to be checked
        q.join()

        # Ensure all threads terminate
        for _ in range(NUM_THREADS):
            q.put(None)
            print("put")
        for t in threads:
            t.join()
            print("join")

        # Step 3: Update MongoDB with valid proxies
        for proxy in valid_proxies:
            collection.update_one(
                {"proxy": proxy},
                {"$set": {"proxy": proxy, "valid": True}},
                upsert=True
            )
            print(f"{proxy} added to db")

        # Step 4: Validate existing proxies in the database
        existing_proxies = collection.find({"valid": True})
        for record in existing_proxies:
            if not validate_proxy(record['proxy']):
                collection.delete_one({"_id": record["_id"]})
                print(f"Removed invalid proxy: {record['proxy']}")

        # Clear valid proxies list for next round
        valid_proxies.clear()

        # Sleep before the next round of crawling and validation
        time.sleep(20)  # Wait before updating again

    client.close()

# Start the proxy updater
update_proxies_in_db()
