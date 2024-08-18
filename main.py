from check_proxies import Crawler
from pymongo import MongoClient

proxy_websites = [
    "https://www.sslproxies.org/",
    "https://free-proxy-list.net/",
    "https://www.us-proxy.org/",
    "https://www.proxy-list.download/HTTPS",
    "https://www.proxynova.com/proxy-server-list/"
]

# Initialize and run the crawler
crawler = Crawler(urls=proxy_websites)
data = crawler.run()

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "ProxyPool"
COLLECTION_NAME = "ProxyLists"

# Establish a connection to MongoDB
client = MongoClient(MONGO_URI)

# Access the database
db = client[DATABASE_NAME]

# Access the collection
collection = db[COLLECTION_NAME]

# Prepare data for MongoDB insertion
if isinstance(data, list):
    for i, document in enumerate(data):
        document["_id"] = f"{document['url'].replace('https://', '').replace('/', '_')}_{i+1}"
    collection.insert_many(data)
else:
    data["_id"] = "single_document_1"
    collection.insert_one(data)

# Print success message
print(f"Data successfully inserted into {DATABASE_NAME}.{COLLECTION_NAME}")

client.close()
