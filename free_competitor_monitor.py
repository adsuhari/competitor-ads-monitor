import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configure logging
logging.basicConfig(level=logging.INFO)

class MetaAdLibraryMonitor:
    def __init__(self):
        self.competitor_urls = [
            "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q=The%20Neon%20Company",
            "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q=NEONTRIP.de",
            "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q=Neonsfeer"
        ]
        self.sheet_name = "Competitor Ads Data"
        
    def scrape_ad_data(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            logging.info(f"Scraped {url} with status {response.status_code}")
            
            if response.status_code != 200:
                logging.error(f"Failed to fetch {url}: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            ad_cards = soup.select('[data-testid="ad-card"]')
            logging.info(f"Found {len(ad_cards)} ad cards on {url}")
            
            ads_data = []
            for card in ad_cards:
                try:
                    ad_text = card.get_text(separator=' ', strip=True)
                    image_url = None
                    image_tag = card.find('img')
                    if image_tag:
                        image_url = image_tag.get('src')
                    
                    ad_data = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'url': url,
                        'ad_text': ad_text[:500],
                        'image_url': image_url,
                        'status': 'SUCCESS'
                    }
                    ads_data.append(ad_data)
                    
                except Exception as e:
                    logging.error(f"Error processing ad card: {e}")
                    continue
            
            return ads_data
        
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return []
    
    def save_to_sheets(self, all_ads_data):
        try:
            creds_json = json.loads(os.getenv('GOOGLE_SHEETS_CREDS'))
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
            client = gspread.authorize(creds)
            
            sheet = client.open(self.sheet_name).sheet1
            
            sheet.clear()
            headers = [
                'Timestamp', 'URL', 'Ad Text', 'Image URL', 'Status'
            ]
            sheet.append_row(headers)
            
            for ad in all_ads_data:
                logging.info(f"Saving ad: {ad.get('ad_text', 'No text')[:50]}...")
                sheet.append_row([
                    ad.get('timestamp', ''),
                    ad.get('url', ''),
                    ad.get('ad_text', ''),
                    ad.get('image_url', ''),
                    ad.get('status', '')
                ])
            
            logging.info(f"Saved {len(all_ads_data)} records to Google Sheets")
        except Exception as e:
            logging.error(f"Google Sheets error: {e}")
    
    def run(self):
        logging.info("Starting Meta Ad Library monitoring")
        all_ads_data = []
        
        for url in self.competitor_urls:
            logging.info(f"Scraping: {url}")
            ads_data = self.scrape_ad_data(url)
            all_ads_data.extend(ads_data)
            logging.info(f"Collected {len(ads_data)} ads from {url}")
        
        if all_ads_data:
            self.save_to_sheets(all_ads_data)
        else:
            logging.warning("No ads collected")

if __name__ == "__main__":
    monitor = MetaAdLibraryMonitor()
    monitor.run()
