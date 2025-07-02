import requests
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class NeonCompetitorMonitor:
    def __init__(self):
        self.competitors = [
            "The Neon Company",
            "NEONTRIP.de",
            "Neonsfeer"
        ]
        self.sheet_name = "Competitor Ads Data"
        
    def fetch_ads(self, competitor):
        url = "https://graph.facebook.com/v18.0/ads_archive"
        params = {
            'search_terms': competitor,
            'ad_reached_countries': 'DE',  # Changed to Germany
            'ad_active_status': 'ALL',
            'limit': 10,
            'fields': 'id,page_name,ad_snapshot_url,funding_entity,ad_creative_bodies,ad_creative_link_titles,ad_creative_link_descriptions,ad_delivery_start_time,ad_delivery_stop_time,impressions,spend,reach'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json().get('data', [])
        except requests.RequestException as e:
            logging.error(f"Error fetching ads for {competitor}: {e}")
            return []
    
    def process_ad_data(self, raw_ads, competitor):
        processed_ads = []
        
        for ad in raw_ads:
            try:
                processed_ad = {
                    'timestamp': datetime.now().isoformat(),
                    'competitor': competitor,
                    'page_name': ad.get('page_name', ''),
                    'ad_id': ad.get('id', ''),
                    'title': self.get_ad_creative_text(ad, 'ad_creative_link_titles'),
                    'body': self.get_ad_creative_text(ad, 'ad_creative_bodies'),
                    'description': self.get_ad_creative_text(ad, 'ad_creative_link_descriptions'),
                    'start_date': ad.get('ad_delivery_start_time', ''),
                    'stop_date': ad.get('ad_delivery_stop_time', ''),
                    'spend': self.format_metrics(ad.get('spend')),
                    'impressions': self.format_metrics(ad.get('impressions')),
                    'reach': self.format_metrics(ad.get('reach')),
                    'url': ad.get('ad_snapshot_url', ''),
                    'status': 'SUCCESS'
                }
                processed_ads.append(processed_ad)
            except Exception as e:
                logging.error(f"Error processing ad: {e}")
                continue
        
        return processed_ads
    
    def get_ad_creative_text(self, ad, field):
        try:
            data = ad.get(field, [])
            return data[0].get('text', '') if data else ''
        except Exception:
            return ''
    
    def format_metrics(self, metric_data):
        if not metric_data:
            return "N/A"
        lower = metric_data.get('lower_bound', '?')
        upper = metric_data.get('upper_bound', '?')
        return f"{lower} - {upper}"
    
    def save_to_sheets(self, data):
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
                'timestamp', 'competitor', 'page_name', 'ad_id',
                'title', 'body', 'description', 'start_date',
                'stop_date', 'spend', 'impressions', 'reach',
                'url', 'status'
            ]
            sheet.append_row(headers)
            
            for row in data:
                sheet.append_row([
                    row.get('timestamp', ''),
                    row.get('competitor', ''),
                    row.get('page_name', ''),
                    row.get('ad_id', ''),
                    row.get('title', ''),
                    row.get('body', ''),
                    row.get('description', ''),
                    row.get('start_date', ''),
                    row.get('stop_date', ''),
                    row.get('spend', ''),
                    row.get('impressions', ''),
                    row.get('reach', ''),
                    row.get('url', ''),
                    row.get('status', '')
                ])
            
            logging.info(f"Saved {len(data)} records to Google Sheets")
        except Exception as e:
            logging.error(f"Google Sheets error: {e}")
    
    def run(self):
        logging.info("Starting neon competitor monitoring")
        all_data = []
        
        for competitor in self.competitors:
            logging.info(f"Processing: {competitor}")
            raw_ads = self.fetch_ads(competitor)
            if raw_ads:
                processed = self.process_ad_data(raw_ads, competitor)
                all_data.extend(processed)
                logging.info(f"Collected {len(processed)} ads for {competitor}")
            else:
                logging.warning(f"No ads found for {competitor}")
        
        if all_data:
            self.save_to_sheets(all_data)
        else:
            logging.warning("No data collected")

if __name__ == "__main__":
    monitor = NeonCompetitorMonitor()
    monitor.run()
