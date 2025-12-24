from scraper import WebScraper

def main():
    config_path = "config.yaml"
    scraper = WebScraper(config_path)
    scraper.run()

if __name__ == "__main__":
    main()
