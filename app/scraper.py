import requests
from bs4 import BeautifulSoup

class WebScraper:
    @staticmethod
    def extract_article_text(url):
        """
        Fetches the webpage and extracts the main text content,
        ignoring scripts, styles, and navigation menus.
        """
        try:
           
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status() 

            soup = BeautifulSoup(response.text, 'html.parser')

            
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()

            
            paragraphs = soup.find_all('p')
            article_content = " ".join([p.get_text() for p in paragraphs])

            
            clean_text = " ".join(article_content.split())

           
            return clean_text[:8000]

        except Exception as e:
            print(f"Scraping Error: {str(e)}")
            return None