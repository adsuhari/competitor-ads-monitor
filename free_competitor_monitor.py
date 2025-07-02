import requests
import json
import os
from datetime import datetime, timedelta
import time
import base64

class EnhancedCompetitorMonitor:
    def __init__(self):
        # CHANGE THESE TO YOUR COMPETITORS
        self.competitors = [
            "Nike",
            "Adidas", 
            "Puma"
        ]
        
        self.sheet_name = "Competitor Ads Data"
        
    def fetch_real_ads_data(self, competitor_name):
        """Fetch actual ads data from Meta Ad Library API"""
        try:
            # Meta Ad Library API (free, no token required for basic data)
            url = "https://graph.facebook.com/v18.0/ads_archive"
            
            params = {
                'search_terms': competitor_name,
                'ad_reached_countries': 'US',
                'ad_active_status': 'ALL',
                'search_page_ids': '',
                'ad_type': 'ALL',
                'media_type': 'ALL',
                'limit': 20,  # Get 20 recent ads
                'fields': 'id,ad_creation_time,ad_creative_bodies,ad_creative_link_captions,ad_creative_link_descriptions,ad_creative_link_titles,ad_snapshot_url,funding_entity,page_name,ad_delivery_start_time,ad_delivery_stop_time,impressions,spend,reach'
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return self.process_ad_data(data.get('data', []), competitor_name)
            else:
                print(f"❌ Error fetching ads for {competitor_name}: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching ads for {competitor_name}: {e}")
            return []
    
    def process_ad_data(self, raw_ads, competitor_name):
        """Process and structure the ad data"""
        processed_ads = []
        
        for ad in raw_ads:
            try:
                # Extract ad creative text
                ad_bodies = ad.get('ad_creative_bodies', [])
                ad_body = ad_bodies[0].get('text', '') if ad_bodies else ''
                
                ad_titles = ad.get('ad_creative_link_titles', [])
                ad_title = ad_titles[0].get('text', '') if ad_titles else ''
                
                ad_descriptions = ad.get('ad_creative_link_descriptions', [])
                ad_description = ad_descriptions[0].get('text', '') if ad_descriptions else ''
                
                ad_captions = ad.get('ad_creative_link_captions', [])
                ad_caption = ad_captions[0].get('text', '') if ad_captions else ''
                
                # Extract metrics
                impressions = ad.get('impressions', {})
                spend = ad.get('spend', {})
                reach = ad.get('reach', {})
                
                # Format impressions range
                impressions_text = ""
                if impressions:
                    lower = impressions.get('lower_bound', 'N/A')
                    upper = impressions.get('upper_bound', 'N/A')
                    impressions_text = f"{lower} - {upper}"
                
                # Format spend range
                spend_text = ""
                if spend:
                    lower = spend.get('lower_bound', 'N/A')
                    upper = spend.get('upper_bound', 'N/A')
                    spend_text = f"${lower} - ${upper}"
                
                # Format reach range
                reach_text = ""
                if reach:
                    lower = reach.get('lower_bound', 'N/A')
                    upper = reach.get('upper_bound', 'N/A')
                    reach_text = f"{lower} - {upper}"
                
                processed_ad = {
                    'date_found': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'competitor': competitor_name,
                    'page_name': ad.get('page_name', ''),
                    'ad_id': ad.get('id', ''),
                    'ad_title': ad_title,
                    'ad_body': ad_body,
                    'ad_description': ad_description,
                    'ad_caption': ad_caption,
                    'creation_time': ad.get('ad_creation_time', ''),
                    'start_time': ad.get('ad_delivery_start_time', ''),
                    'stop_time': ad.get('ad_delivery_stop_time', ''),
                    'impressions': impressions_text,
                    'spend': spend_text,
                    'reach': reach_text,
                    'snapshot_url': ad.get('ad_snapshot_url', ''),
                    'funding_entity': ad.get('funding_entity', '')
                }
                
                processed_ads.append(processed_ad)
                
            except Exception as e:
                print(f"❌ Error processing ad: {e}")
                continue
        
        return processed_ads
    
    def download_ad_creative(self, snapshot_url, ad_id):
        """Download ad creative image"""
        try:
            if not snapshot_url:
                return None
                
            response = requests.get(snapshot_url)
            if response.status_code == 200:
                # Convert to base64 for storage
                image_data = base64.b64encode(response.content).decode()
                return f"data:image/png;base64,{image_data[:100]}..."  # Truncated for display
            
        except Exception as e:
            print(f"❌ Error downloading creative for {ad_id}: {e}")
            
        return None
    
    def save_to_google_sheets(self, all_ads_data):
        """Save enhanced data to Google Sheets"""
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            creds_json = json.loads(os.getenv('GOOGLE_SHEETS_CREDS'))
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
            client = gspread.authorize(creds)
            
            sheet = client.open(self.sheet_name).sheet1
            
            # Enhanced headers
            headers = [
                'Date Found', 'Competitor', 'Page Name', 'Ad ID', 'Ad Title', 
                'Ad Body', 'Ad Description', 'Ad Caption', 'Creation Time', 
                'Start Time', 'Stop Time', 'Impressions', 'Spend', 'Reach', 
                'Snapshot URL', 'Funding Entity'
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
                    ad.get('ad_title', ''),
                    ad.get('ad_body', ''),
                    ad.get('ad_description', ''),
                    ad.get('ad_caption', ''),
                    ad.get('creation_time', ''),
                    ad.get('start_time', ''),
                    ad.get('stop_time', ''),
                    ad.get('impressions', ''),
                    ad.get('spend', ''),
                    ad.get('reach', ''),
                    ad.get('snapshot_url', ''),
                    ad.get('funding_entity', '')
                ]
                sheet.append_row(row)
            
            print(f"✅ Saved {len(all_ads_data)} ads with full data to Google Sheets")
            
        except Exception as e:
            print(f"❌ Error saving to sheets: {e}")
            # Print data for debugging
            print("📊 Collected ads data:")
            for ad in all_ads_data[:3]:  # Show first 3 for debugging
                print(f"   🎯 {ad.get('competitor')} - {ad.get('ad_title', 'No title')}")
                print(f"      💰 Spend: {ad.get('spend', 'N/A')}")
                print(f"      👀 Impressions: {ad.get('impressions', 'N/A')}")
                print(f"      📝 Body: {ad.get('ad_body', 'No body')[:100]}...")
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
                        "name": "Active Campaigns",
                        "value": str(summary.get('active_campaigns', 0)),
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
            print(f"📊 Fetching real ads for {competitor}...")
            
            # Get actual ad data from Meta Ad Library
            competitor_ads = self.fetch_real_ads_data(competitor)
            all_ads_data.extend(competitor_ads)
            
            print(f"   ✅ Found {len(competitor_ads)} ads for {competitor}")
            
            # Small delay to be respectful to the API
            time.sleep(2)
        
        # Save enhanced data
        self.save_to_google_sheets(all_ads_data)
        
        # Generate summary
        summary = {
            'total_ads': len(all_ads_data),
            'competitors_count': len(self.competitors),
            'active_campaigns': len(set(ad.get('page_name', '') for ad in all_ads_data))
        }
        
        # Send enhanced notification
        self.send_enhanced_notification(summary)
        
        print(f"✅ Enhanced monitoring complete!")
        print(f"📊 Total ads collected: {len(all_ads_data)}")
        print(f"📝 Check your Google Sheet: {self.sheet_name}")
        
        # Print sample data
        if all_ads_data:
            print("\n🎯 Sample ad data:")
            sample_ad = all_ads_data[0]
            print(f"   Competitor: {sample_ad.get('competitor')}")
            print(f"   Title: {sample_ad.get('ad_title', 'No title')}")
            print(f"   Spend: {sample_ad.get('spend', 'N/A')}")
            print(f"   Impressions: {sample_ad.get('impressions', 'N/A')}")

if __name__ == "__main__":
    monitor = EnhancedCompetitorMonitor()
    monitor.run_enhanced_monitor()
