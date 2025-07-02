import requests
import json
import os
from datetime import datetime
import time
import re

class EnhancedCompetitorMonitor:
    def __init__(self):
        # YOUR COMPETITORS
        self.competitors = [
            "The Neon Company",
            "NEONTRIP.de",
            "Neonsfeer"
        ]
        
        self.sheet_name = "Competitor Ads Data"
        
    def fetch_real_ads_data(self, competitor_name):
        """Fetch actual ads data from Meta Ad Library API (public endpoint)"""
        try:
            # Using the public Meta Ad Library endpoint that doesn't require authentication
            url = "https://graph.facebook.com/v18.0/ads_archive"
            
            params = {
                'search_terms': competitor_name,
                'ad_reached_countries': 'US,GB,DE,NL',  # Multiple countries for better results
                'ad_active_status': 'ALL',
                'limit': 50,  # Increased limit
                # Simplified fields that work without token
                'fields': 'id,ad_snapshot_url,page_name,funding_entity,ad_creation_time'
            }
            
            response = requests.get(url, params=params, timeout=30)
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Raw API response: {json.dumps(data, indent=2)[:500]}...")
                
                if 'data' in data and data['data']:
                    return self.process_ad_data(data['data'], competitor_name)
                else:
                    print(f"No ads found in API response for {competitor_name}")
                    return []
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching ads for {competitor_name}: {e}")
            return []
    
    def scrape_ad_details(self, snapshot_url):
        """Scrape additional details from the snapshot URL"""
        try:
            if not snapshot_url:
                return {}
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(snapshot_url, headers=headers, timeout=15)
            if response.status_code == 200:
                html_content = response.text
                
                # Extract ad text using regex patterns
                ad_text = ""
                
                # Look for common ad text patterns
                text_patterns = [
                    r'"body":\s*"([^"]+)"',
                    r'"primary_text":\s*"([^"]+)"',
                    r'data-testid="ad-text"[^>]*>([^<]+)',
                    r'<div[^>]*class="[^"]*ad[^"]*text[^"]*"[^>]*>([^<]+)'
                ]
                
                for pattern in text_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    if matches:
                        ad_text = matches[0].strip()
                        break
                
                return {
                    'ad_text': ad_text[:500] if ad_text else 'Text extraction unavailable',
                    'extracted_from_snapshot': True
                }
                
        except Exception as e:
            print(f"Error scraping snapshot: {e}")
            
        return {'ad_text': 'Unable to extract text', 'extracted_from_snapshot': False}
    
    def process_ad_data(self, raw_ads, competitor_name):
        """Process and structure the ad data"""
        processed_ads = []
        
        print(f"Processing {len(raw_ads)} ads for {competitor_name}")
        
        for i, ad in enumerate(raw_ads):
            try:
                print(f"Processing ad {i+1}: {ad}")
                
                # Get basic ad info
                ad_id = ad.get('id', '')
                page_name = ad.get('page_name', '')
                snapshot_url = ad.get('ad_snapshot_url', '')
                creation_time = ad.get('ad_creation_time', '')
                funding_entity = ad.get('funding_entity', '')
                
                # Try to get additional details from snapshot
                snapshot_details = self.scrape_ad_details(snapshot_url)
                
                processed_ad = {
                    'date_found': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'competitor': competitor_name,
                    'page_name': page_name,
                    'ad_id': ad_id,
                    'ad_text': snapshot_details.get('ad_text', 'Text not available'),
                    'creation_time': creation_time,
                    'funding_entity': funding_entity,
                    'snapshot_url': snapshot_url,
                    'data_source': 'Meta Ad Library API + Snapshot Scraping'
                }
                
                processed_ads.append(processed_ad)
                print(f"✅ Processed ad: {page_name} - {ad_id}")
                
                # Small delay between snapshot requests
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing ad {i+1}: {e}")
                continue
        
        return processed_ads
    
    def save_to_google_sheets(self, all_ads_data):
        """Save enhanced data to Google Sheets"""
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            print(f"Attempting to save {len(all_ads_data)} ads to Google Sheets")
            
            creds_json = json.loads(os.getenv('GOOGLE_SHEETS_CREDS'))
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
            client = gspread.authorize(creds)
            
            sheet = client.open(self.sheet_name).sheet1
            
            # Enhanced headers
            headers = [
                'Date Found', 'Competitor', 'Page Name', 'Ad ID', 'Ad Text', 
                'Creation Time', 'Funding Entity', 'Snapshot URL', 'Data Source'
            ]
            
            # Clear and add headers
            sheet.clear()
            sheet.append_row(headers)
            
            # Add all ads data
            for ad in all_ads_data:
                row = [
                    ad.get('date_found', ''),
                    ad.get('competitor', ''),
                    ad.get('page_name', ''),
                    ad.get('ad_id', ''),
                    ad.get('ad_text', ''),
                    ad.get('creation_time', ''),
                    ad.get('funding_entity', ''),
                    ad.get('snapshot_url', ''),
                    ad.get('data_source', '')
                ]
                sheet.append_row(row)
            
            print(f"✅ Saved {len(all_ads_data)} ads with data to Google Sheets")
            
        except Exception as e:
            print(f"❌ Error saving to sheets: {e}")
            print("📊 Collected ads data (fallback display):")
            for ad in all_ads_data:
                print(f"   🎯 {ad.get('competitor')} - {ad.get('page_name', 'Unknown Page')}")
                print(f"      📝 Text: {ad.get('ad_text', 'No text')[:100]}...")
                print(f"      🔗 URL: {ad.get('snapshot_url', 'No URL')}")
                print()
    
    def send_enhanced_notification(self, summary):
        """Send enhanced notification with real metrics"""
        webhook_url = os.getenv('DISCORD_WEBHOOK')
        
        if not webhook_url or webhook_url == 'optional':
            print("No Discord webhook configured - skipping notification")
            return
        
        message = {
            "content": f"🔍 **Enhanced Competitor Report** - {datetime.now().strftime('%Y-%m-%d')}",
            "embeds": [{
                "title": "Real Ad Data Collected",
                "color": 3447003,
                "fields": [
                    {
                        "name": "Total Ads Found",
                        "value": str(summary.get('total_ads', 0)),
                        "inline": True
                    },
                    {
                        "name": "Competitors Monitored",
                        "value": str(summary.get('competitors_count', 0)),
                        "inline": True
                    },
                    {
                        "name": "Pages Found",
                        "value": str(summary.get('unique_pages', 0)),
                        "inline": True
                    }
                ]
            }]
        }
        
        try:
            response = requests.post(webhook_url, json=message)
            print("✅ Enhanced Discord notification sent")
        except Exception as e:
            print(f"❌ Discord notification failed: {e}")
    
    def run_enhanced_monitor(self):
        """Main execution with real ad data collection"""
        print(f"🚀 Starting enhanced competitor monitoring at {datetime.now()}")
        all_ads_data = []
        
        for competitor in self.competitors:
            print(f"\n📊 Fetching real ads for {competitor}...")
            
            # Get actual ad data from Meta Ad Library
            competitor_ads = self.fetch_real_ads_data(competitor)
            all_ads_data.extend(competitor_ads)
            
            print(f"   ✅ Found {len(competitor_ads)} ads for {competitor}")
            
            # Delay between competitors
            time.sleep(3)
        
        print(f"\n📊 Total ads collected: {len(all_ads_data)}")
        
        if all_ads_data:
            # Save enhanced data
            self.save_to_google_sheets(all_ads_data)
            
            # Generate summary
            summary = {
                'total_ads': len(all_ads_data),
                'competitors_count': len(self.competitors),
                'unique_pages': len(set(ad.get('page_name', '') for ad in all_ads_data if ad.get('page_name')))
            }
            
            # Send enhanced notification
            self.send_enhanced_notification(summary)
            
            print(f"✅ Enhanced monitoring complete!")
            print(f"📝 Check your Google Sheet: {self.sheet_name}")
            
            # Print sample data
            print("\n🎯 Sample ad data:")
            for ad in all_ads_data[:2]:
                print(f"   Competitor: {ad.get('competitor')}")
                print(f"   Page: {ad.get('page_name', 'Unknown')}")
                print(f"   Text: {ad.get('ad_text', 'No text')[:100]}...")
                print(f"   URL: {ad.get('snapshot_url', 'No URL')}")
                print()
        else:
            print("❌ No ads found for any competitors")
            print("This could be because:")
            print("   - Competitors don't have active ads in the specified countries")
            print("   - Company names don't match exactly in Meta Ad Library")
            print("   - API rate limiting or temporary issues")

if __name__ == "__main__":
    monitor = EnhancedCompetitorMonitor()
    monitor.run_enhanced_monitor()
