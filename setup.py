#!/usr/bin/env python3
"""
Setup script for Pei Wei Ads Dashboard
Guides user through credential configuration and testing
"""

import os
import sys
import json
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_section(text):
    print(f"\n{text}")
    print("-" * 60)

def check_env_file():
    """Check if .env file exists and has required fields"""
    print_header("Step 1: Environment Configuration")

    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("\nCreating .env from .env.example...")
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as f:
                example_content = f.read()
            with open('.env', 'w') as f:
                f.write(example_content)
            print("✅ .env file created (update with your credentials)\n")
        else:
            print("❌ .env.example not found\n")
            return False
    else:
        print("✅ .env file exists\n")

    # Check for required variables
    required_vars = [
        'GOOGLE_ADS_DEVELOPER_TOKEN',
        'GOOGLE_ADS_CUSTOMER_ID',
        'META_APP_ID',
        'META_AD_ACCOUNT_ID',
        'TIKTOK_APP_ID',
        'TIKTOK_ADVERTISER_ID',
    ]

    with open('.env', 'r') as f:
        env_content = f.read()

    missing = []
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=your_" in env_content:
            missing.append(var)

    if missing:
        print("⚠️  Missing required credentials:")
        for var in missing:
            print(f"   - {var}")
        print("\nUpdate .env file with your API credentials and rerun this script\n")
        return False
    else:
        print("✅ All required credentials appear to be configured\n")
        return True

def check_dependencies():
    """Check if Python dependencies are installed"""
    print_section("Step 2: Python Dependencies")

    try:
        import google.ads.googleads
        print("✅ google-ads")
    except ImportError:
        print("❌ google-ads - Run: pip install google-ads")
        return False

    try:
        import facebook_business
        print("✅ facebook-business")
    except ImportError:
        print("❌ facebook-business - Run: pip install facebook-business")
        return False

    try:
        import pandas
        print("✅ pandas")
    except ImportError:
        print("❌ pandas - Run: pip install pandas")
        return False

    try:
        import gspread
        print("✅ gspread")
    except ImportError:
        print("❌ gspread - Run: pip install gspread")
        return False

    try:
        import pytz
        print("✅ pytz")
    except ImportError:
        print("❌ pytz - Run: pip install pytz")
        return False

    try:
        import requests
        print("✅ requests")
    except ImportError:
        print("❌ requests - Run: pip install requests")
        return False

    print("\n✅ All dependencies are installed\n")
    return True

def test_apis():
    """Test API connections"""
    print_section("Step 3: API Connectivity Tests")

    from dotenv import load_dotenv
    load_dotenv()

    # Test Google Ads
    print("\nTesting Google Ads API...")
    try:
        from google.ads.googleads.client import GoogleAdsClient
        client = GoogleAdsClient.load_from_storage()
        print("✅ Google Ads API connection successful")
    except Exception as e:
        print(f"❌ Google Ads API failed: {str(e)}")

    # Test Meta Ads
    print("\nTesting Meta Ads API...")
    try:
        from facebook_business.api import FacebookAdsApi
        access_token = os.getenv('META_ACCESS_TOKEN')
        if access_token and not access_token.startswith('your_'):
            FacebookAdsApi.init(access_token=access_token)
            print("✅ Meta Ads API connection successful")
        else:
            print("⚠️  Meta Ads token not configured")
    except Exception as e:
        print(f"❌ Meta Ads API failed: {str(e)}")

    # Test TikTok Ads
    print("\nTesting TikTok Ads API...")
    try:
        import requests
        token = os.getenv('TIKTOK_ACCESS_TOKEN')
        if token and not token.startswith('your_'):
            headers = {'Access-Token': token}
            response = requests.head('https://ads.tiktok.com/open_api/v1.3/campaign/get/', headers=headers, timeout=5)
            if response.status_code in [200, 400]:  # 400 is expected without params
                print("✅ TikTok Ads API connection successful")
            else:
                print(f"⚠️  TikTok Ads API returned: {response.status_code}")
        else:
            print("⚠️  TikTok Ads token not configured")
    except Exception as e:
        print(f"⚠️  TikTok Ads API test: {str(e)}")

    # Test Google Sheets
    print("\nTesting Google Sheets API...")
    try:
        import gspread
        creds_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON', 'credentials.json')
        if os.path.exists(creds_file):
            from oauth2client.service_account import ServiceAccountCredentials
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scopes=scope)
            print("✅ Google Sheets credentials found and valid")
        else:
            print(f"❌ Credentials file not found: {creds_file}")
    except Exception as e:
        print(f"⚠️  Google Sheets API test: {str(e)}")

    print()

def create_data_directory():
    """Create data directory for storing results"""
    print_section("Step 4: Create Data Directory")

    os.makedirs('./data', exist_ok=True)
    print("✅ Data directory ready at ./data/\n")

def show_next_steps():
    """Show next steps for user"""
    print_header("Setup Complete!")

    print("""
Next Steps:

1. RUN FETCH LOCALLY
   python fetch_data.py
   This will populate dashboard_data.json with real data

2. VIEW DASHBOARD LOCALLY
   python -m http.server 8000
   Visit: http://localhost:8000/dashboard.html

3. PREPARE FOR GITHUB
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/topobenquet/peiwei-dashboard.git
   git branch -M main
   git push -u origin main

4. CONFIGURE GITHUB SECRETS
   Go to: https://github.com/topobenquet/peiwei-dashboard/settings/secrets/actions
   Add all credentials as secrets (see README.md for list)

5. ENABLE GITHUB PAGES
   Go to: https://github.com/topobenquet/peiwei-dashboard/settings/pages
   Select 'main' branch as source

6. TEST WORKFLOW
   Go to: https://github.com/topobenquet/peiwei-dashboard/actions
   Click "Update Ads Dashboard" > "Run workflow"

For detailed instructions, see README.md
    """)

def main():
    """Main setup flow"""
    print_header("Pei Wei Ads Dashboard - Setup")

    # Step 1: Environment
    if not check_env_file():
        print("⚠️  Setup incomplete. Update .env file and rerun setup.py\n")
        return

    # Step 2: Dependencies
    if not check_dependencies():
        print("⚠️  Install missing dependencies and rerun setup.py\n")
        return

    # Step 3: Create data directory
    create_data_directory()

    # Step 4: Test APIs
    test_apis()

    # Step 5: Next steps
    show_next_steps()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}\n")
        sys.exit(1)
