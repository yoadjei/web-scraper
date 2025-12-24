import time
import requests
import yaml
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class WebScraper:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.base_url = self.config['base_url']
        self.output_format = self.config['output_format']
        self.output_file = self.config['output_file']
        self.selectors = self.config['selectors']
        self.pagination_config = self.config.get('pagination', {})
        self.sess = requests.Session()
    
    def fetch_page(self, url):
        retries = self.config.get('max_retries', 3)
        delay = self.config.get('rate_limit_delay', 1.0)
        
        for attempt in range(retries):
            try:
                # Rate limiting
                time.sleep(delay)
                
                response = self.sess.get(url)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {attempt+1}/{retries} failed for {url}: {e}")
                if attempt == retries - 1:
                    print(f"Max retries reached for {url}")
                    return None
        return None

    def parse_page(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        container_selector = self.selectors['item_container']
        containers = soup.select(container_selector)
        
        for container in containers:
            item = {}
            for field, selector_str in self.selectors['fields'].items():
                # Handle attribute selection like "::attr(title)"
                if "::attr(" in selector_str:
                    selector, attr_part = selector_str.split("::attr(")
                    attr_name = attr_part.rstrip(")")
                    element = container.select_one(selector)
                    value = element[attr_name] if element and element.has_attr(attr_name) else None
                elif "::text" in selector_str:
                    selector = selector_str.replace("::text", "")
                    element = container.select_one(selector)
                    value = element.get_text(strip=True) if element else None
                else:
                    element = container.select_one(selector_str)
                    value = element.get_text(strip=True) if element else None
                
                item[field] = value
            items.append(item)
            
        return items, soup

    def get_next_page(self, current_url, soup):
        strategy = self.pagination_config.get('strategy')
        
        if strategy == "next_button":
            next_selector = self.pagination_config.get('next_button_selector')
            if not next_selector:
                return None
            
            next_link = soup.select_one(next_selector)
            if next_link and next_link.has_attr('href'):
                return urljoin(current_url, next_link['href'])
        
        return None

    def run(self):
        all_data = []
        current_url = self.base_url
        max_pages = self.pagination_config.get('max_pages', 5)
        pages_scraped = 0
        
        print(f"Starting scrape on {self.base_url}")
        
        while current_url and pages_scraped < max_pages:
            print(f"Scraping page {pages_scraped + 1}: {current_url}")
            html = self.fetch_page(current_url)
            
            if not html:
                break
            
            items, soup = self.parse_page(html)
            all_data.extend(items)
            print(f"Found {len(items)} items")
            
            current_url = self.get_next_page(current_url, soup)
            pages_scraped += 1
            
        self.save_data(all_data)
        print("Scraping finished.")

    def save_data(self, data):
        df = pd.DataFrame(data)
        
        if self.output_format == 'csv':
            filename = f"{self.output_file}.csv"
            df.to_csv(filename, index=False)
        elif self.output_format == 'json':
            filename = f"{self.output_file}.json"
            df.to_json(filename, orient='records', indent=2)
        elif self.output_format == 'parquet':
            filename = f"{self.output_file}.parquet"
            df.to_parquet(filename, index=False)
        else:
            print(f"Unknown output format: {self.output_format}")
            return
            
        print(f"Data saved to {filename}")
