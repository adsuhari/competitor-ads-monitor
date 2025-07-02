import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class MetaAdLibraryMonitor:
    def __init__(self):
        # META AD LIBRARY URLS FOR COMPETITORS
        self.competitor_urls = [
            "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=112878497257448",
            "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=106647571366212",
            "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=107482391640789"
        ]
        self.sheet_name = "Competitor Ads Data"
        
    def scrape_ad_data(self, url):
        """Scrape ad data from Meta Ad Library URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logging.error(f"Failed to fetch {url}: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract ad cards
            ad_cards = soup.select('[data-testid="ad-card"]')
            
            ads_data = []
            for card in ad_cards:
                try:
                    # Extract ad creative text
                    ad_text = card.get_text(separator=' ', strip=True)
                    
                    # Extract snapshot image (if available)
                    image_url = None
                    image_tag = card.find('img')
                    if image_tag:
                        image_url = image_tag.get('src')
                    
                    ad_data = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'url': url,
                        'ad_text': ad_text[:500],  # Truncate for storage
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
        """Save data to Google Sheets"""
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            creds_json = json.loads(os.getenv('GOOGLE_SHEETS_CREDS'))
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
            client = gspread.authorize(creds)
            
            sheet = client.open(self.sheet_name).sheet1
            
            # Clear existing data
            sheet.clear()
            
            headers = [
                'Timestamp', 'URL', 'Ad Text', 'Image URL', 'Status'
            ]
            sheet.append_row(headers)
            
            for ad in all_ads_data:
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
