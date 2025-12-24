# Web Scraper 

A configurable web scraper built with Python.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Configure**: Open `config.yaml`.
   - Set `base_url` to your target website (default: `http://books.toscrape.com/`).
   - Update `selectors` to match the site's HTML structure.
2. **Run**:
   ```bash
   python main.py
   ```
3. **Output**: Data is saved to `books_data.csv` (configurable).
