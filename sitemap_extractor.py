import cloudscraper
import xml.etree.ElementTree as ET
import concurrent.futures
import time
import requests

def extract_and_save_links(sitemap_url, file):
    """
    Fetches a sitemap, extracts links, and saves them to the given file.
    """
    retries = 3
    for i in range(retries):
        try:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(sitemap_url)
            if response.status_code == 404:
                print(f"Sitemap {sitemap_url} not found (404). Skipping.")
                return
            response.raise_for_status()
            root = ET.fromstring(response.content)
            links = []
            for url_element in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc = url_element.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None:
                    links.append(loc.text)
            
            for link in links:
                file.write(f"{link}\n")
            return # Success

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 500:
                print(f"Server error (500) for {sitemap_url}. Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"HTTP error for {sitemap_url}: {e}")
                return
        except Exception as e:
            print(f"Error processing sitemap {sitemap_url}: {e}")
            return

if __name__ == "__main__":
    sitemap_urls = [f"https://viralkand.com/post-sitemap{i}.xml" for i in range(1, 15)]
    output_filename = "sitemap_links.txt"

    with open(output_filename, 'w') as f:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(extract_and_save_links, url, f) for url in sitemap_urls]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"An error occurred: {e}")

    print(f"Extraction complete. Links saved to {output_filename}")