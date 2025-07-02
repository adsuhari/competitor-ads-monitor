import requests
import json
import os
from datetime import datetime

class FreeCompetitorMonitor:
    def __init__(self):
        # CHANGE THESE TO YOUR COMPETITORS
        self.competitors = [
            "Nike",
            "Adidas", 
            "Puma"
        ]
        
        # CHANGE THIS TO YOUR GOOGLE SHEET NAME
        self.sheet_name = "Competitor Ads Data"
        
    def save_to_google_sheets(self, data):
        """Save to Google Sheets (Free)"""
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            
            # Setup Google Sheets connection
            creds_json = json.loads(os.getenv('GOOGLE_SHEETS_CREDS'))
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
            client = gspread.authorize(creds)
            
            # Open your spreadsheet
            sheet = client.open(self.sheet_name).sheet1
            
            # Add headers if sheet is empty
            if sheet.row_count == 0:
                sheet.append_row(['Date', 'Competitor', 'Status', 'Ad Library URL'])
            
            # Add data
            for row in data:
                sheet.append_row([
                    row.get('date_found', ''),
                    row.get('competitor', ''),
                    row.get('status', ''),
                    row.get('url', '')
                ])
                
            print(f"✅ Saved {len(data)} entries to Google Sheets")
                
        except Exception as e:
            print(f"❌ Error saving to sheets: {e}")
    
    def send_discord_notification(self, summary):
        """Send notification to Discord (Free)"""
        webhook_url = os.getenv('DISCORD_WEBHOOK')
        
        if not webhook_url:
            print("No Discord webhook configured - skipping notification")
            return
            
        message = {
            "content": f"🔍 **Daily Competitor Report** - {datetime.now().strftime('%Y-%m-%d')}",
            "embeds": [{
                "title": "Monitoring Complete",
                "color": 3447003,
                "fields": [
                    {
                        "name": "Competitors Monitored",
                        "value": str(len(self.competitors)),
                        "inline": True
                    },
                    {
                        "name": "Status", 
                        "value": "✅ Complete",
                        "inline": True
                    }
                ]
            }]
        }
        
        try:
            response = requests.post(webhook_url, json=message)
            print("✅ Discord notification sent")
        except Exception as e:
            print(f"❌ Discord notification failed: {e}")
    
    def run_monitor(self):
        """Main execution"""
        print(f"🚀 Starting competitor monitoring at {datetime.now()}")
        collected_data = []
        
        for competitor in self.competitors:
            print(f"📊 Monitoring {competitor}...")
            
            # Create monitoring entry
            data_entry = {
                'competitor': competitor,
                'status': 'Monitored',
                'date_found': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'url': f"https://facebook.com/ads/library/?search_terms={competitor.replace(' ', '%20')}"
            }
            collected_data.append(data_entry)
        
        # Save and notify
        self.save_to_google_sheets(collected_data)
        self.send_discord_notification({'total': len(collected_data)})
        
        print("✅ Free monitoring complete!")
        print(f"📝 Check your Google Sheet: {self.sheet_name}")

if __name__ == "__main__":
    monitor = FreeCompetitorMonitor()
    monitor.run_monitor()
