from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

class Crawler:
    def __init__(self, urls, max_scrolls=50, pause_time=2, max_links=5, output_file='proxies.json'):
        self.urls = urls
        self.max_scrolls = max_scrolls
        self.pause_time = pause_time
        self.max_links = max_links
        self.output_file = output_file

        # Set up Chrome options
        options = Options()
        options.add_argument("--headless")
        options.add_experimental_option("detach", True)  # Keep the browser open after the script finishes

        # Initialize the WebDriver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def extract_proxies_from_table(self):
        proxies = []  # List to hold the extracted proxies

        # Find all th elements and locate the table containing "Proxy IP" or "IP Address"
        th_elements = self.driver.find_elements(By.TAG_NAME, 'th')
        for th in th_elements:
            if "Proxy IP" in th.text or "IP Address" in th.text:
                table = th.find_element(By.XPATH, "./ancestor::table")
                if table:
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    for row in rows[1:]:  # Skip the header row
                        cols = row.find_elements(By.TAG_NAME, 'td')
                        if len(cols) >= 2:  # Ensure there are at least two columns
                            ip = cols[0].text.strip()
                            port = cols[1].text.strip()
                            if ip and port:
                                proxies.append(f"{ip}:{port}")
                break

        return proxies

    def crawl_and_extract_data(self):
        data = []  # List to hold all the data

        # Process each URL in the provided list
        for url in self.urls:
            page_data = {"url": url, "proxies": []}  # Dictionary to store data for each page

            try:
                self.driver.get(url)
                time.sleep(2)  # Adjust the wait time as needed

                # Extract proxies from the table
                proxies = self.extract_proxies_from_table()
                if proxies:
                    page_data["proxies"] = proxies
                    data.append(page_data)  # Add the page data to the main list only if proxies are found

            except Exception as e:
                print(f"Error processing {url}: {str(e)}")

        return data

    def run(self):
        # Crawl and extract data from the provided URLs
        data = self.crawl_and_extract_data()

        # Save the data to a JSON file
        with open(self.output_file, 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        # Close the browser window (comment this out if you want to keep the browser open)
        self.driver.quit()

        return data
