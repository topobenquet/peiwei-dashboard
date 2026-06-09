#!/usr/bin/env python3
"""
Fetch ad performance data from Google Ads, Meta Ads, and TikTok Ads APIs.
Exports data to Google Sheets and generates dashboard data.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import csv

import pandas as pd
import pytz
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from facebook_business.api import FacebookAdsApi
from facebook_business.objects import AdAccount, Campaign
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
ET = pytz.timezone('America/New_York')
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
HISTORICAL_DATA_FILE = os.getenv('HISTORICAL_DATA_FILE', './data/historical_data.csv')

# Budget configuration for June (in USD)
BUDGET_CONFIG = {
    'Google Search': 18600,
    'Google PMax': 25200,
    'Meta Ads': 19300,
    'TikTok': 1900,
}

# Ensure data directory exists
os.makedirs('./data', exist_ok=True)


class GoogleAdsDataFetcher:
    """Fetch data from Google Ads API."""

    def __init__(self):
        try:
            self.client = GoogleAdsClient.load_from_storage()
            self.customer_id = os.getenv('GOOGLE_ADS_CUSTOMER_ID', '934-886-7971').replace('-', '')
            logger.info("Google Ads client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Ads client: {e}")
            self.client = None

    def fetch_campaigns(self) -> Dict:
        """Fetch campaign metrics from Google Ads."""
        if not self.client:
            logger.warning("Google Ads client not available")
            return {}

        try:
            ga_service = self.client.get_service("GoogleAdsService")

            query = """
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversion_value
                FROM campaign
                WHERE segments.date DURING LAST_30_DAYS
                ORDER BY metrics.cost_micros DESC
            """

            request = self.client.build_client_request(
                self.client.get_service("GoogleAdsService"),
                customer_id=self.customer_id,
                query=query
            )

            results = {}
            for row in ga_service.search_stream(request):
                campaign = row.campaign
                metrics = row.metrics

                campaign_name = campaign.name
                cost_usd = metrics.cost_micros / 1_000_000

                results[campaign_name] = {
                    'platform': 'Google Ads',
                    'campaign_id': campaign.id,
                    'impressions': metrics.impressions,
                    'clicks': metrics.clicks,
                    'spend_usd': cost_usd,
                    'conversions': metrics.conversions,
                    'conversion_value': metrics.conversion_value / 1_000_000 if metrics.conversion_value else 0,
                    'ctr': (metrics.clicks / metrics.impressions * 100) if metrics.impressions > 0 else 0,
                    'cpa': (cost_usd / metrics.conversions) if metrics.conversions > 0 else 0,
                    'roas': (metrics.conversion_value / metrics.cost_micros) if metrics.cost_micros > 0 else 0,
                }

            logger.info(f"Fetched {len(results)} Google Ads campaigns")
            return results

        except Exception as e:
            logger.error(f"Error fetching Google Ads data: {e}")
            return {}


class MetaAdsDataFetcher:
    """Fetch data from Meta Ads API."""

    def __init__(self):
        try:
            access_token = os.getenv('META_ACCESS_TOKEN')
            app_secret = os.getenv('META_APP_SECRET')
            FacebookAdsApi.init(access_token=access_token)
            self.ad_account_id = os.getenv('META_AD_ACCOUNT_ID', '242286109226006')
            logger.info("Meta Ads client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Meta Ads client: {e}")
            self.ad_account_id = None

    def fetch_campaigns(self) -> Dict:
        """Fetch campaign metrics from Meta Ads."""
        if not self.ad_account_id:
            logger.warning("Meta Ads account ID not available")
            return {}

        try:
            ad_account = AdAccount(f'act_{self.ad_account_id}')
            campaigns = ad_account.get_campaigns(fields=[
                Campaign.Field.id,
                Campaign.Field.name,
                Campaign.Field.status,
            ])

            results = {}
            for campaign in campaigns:
                insights = campaign.get_insights(
                    fields=[
                        'spend',
                        'impressions',
                        'clicks',
                        'actions',
                        'action_values',
                        'action_type',
                    ],
                    date_preset='last_30d'
                )

                spend = sum(float(i.get('spend', 0)) for i in insights)
                impressions = sum(int(i.get('impressions', 0)) for i in insights)
                clicks = sum(int(i.get('clicks', 0)) for i in insights)
                conversions = sum(
                    int(a.get('value', 0))
                    for i in insights
                    for a in i.get('actions', [])
                    if a.get('action_type') == 'purchase'
                )
                conversion_value = sum(
                    float(v.get('value', 0))
                    for i in insights
                    for v in i.get('action_values', [])
                    if v.get('action_type') == 'purchase'
                )

                results[campaign[Campaign.Field.name]] = {
                    'platform': 'Meta Ads',
                    'campaign_id': campaign[Campaign.Field.id],
                    'impressions': impressions,
                    'clicks': clicks,
                    'spend_usd': spend,
                    'conversions': conversions,
                    'conversion_value': conversion_value,
                    'ctr': (clicks / impressions * 100) if impressions > 0 else 0,
                    'cpa': (spend / conversions) if conversions > 0 else 0,
                    'roas': (conversion_value / spend) if spend > 0 else 0,
                }

            logger.info(f"Fetched {len(results)} Meta Ads campaigns")
            return results

        except Exception as e:
            logger.error(f"Error fetching Meta Ads data: {e}")
            return {}


class TikTokAdsDataFetcher:
    """Fetch data from TikTok Ads API."""

    def __init__(self):
        self.access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
        self.advertiser_id = os.getenv('TIKTOK_ADVERTISER_ID', '7099894550273081346')
        self.base_url = 'https://ads.tiktok.com/open_api/v1.3'
        logger.info("TikTok Ads client initialized")

    def fetch_campaigns(self) -> Dict:
        """Fetch campaign metrics from TikTok Ads."""
        if not self.access_token:
            logger.warning("TikTok access token not available")
            return {}

        try:
            headers = {
                'Access-Token': self.access_token,
                'Content-Type': 'application/json',
            }

            # Get campaigns
            campaign_url = f'{self.base_url}/campaign/get/'
            campaign_params = {
                'advertiser_id': self.advertiser_id,
                'page_size': 100,
            }

            campaign_response = requests.get(
                campaign_url,
                headers=headers,
                params=campaign_params,
                timeout=10
            )
            campaign_response.raise_for_status()
            campaigns = campaign_response.json().get('data', {}).get('campaigns', [])

            results = {}

            for campaign in campaigns:
                campaign_id = campaign['campaign_id']
                campaign_name = campaign['campaign_name']

                # Get insights for each campaign
                insights_url = f'{self.base_url}/ad/get/'
                insights_params = {
                    'advertiser_id': self.advertiser_id,
                    'campaign_id': campaign_id,
                    'page_size': 100,
                }

                insights_response = requests.get(
                    insights_url,
                    headers=headers,
                    params=insights_params,
                    timeout=10
                )

                if insights_response.status_code == 200:
                    ads = insights_response.json().get('data', {}).get('ads', [])

                    spend = sum(float(ad.get('budget', 0)) for ad in ads)
                    impressions = sum(int(ad.get('stat', {}).get('impressions', 0)) for ad in ads)
                    clicks = sum(int(ad.get('stat', {}).get('clicks', 0)) for ad in ads)
                    conversions = sum(int(ad.get('stat', {}).get('conversions', 0)) for ad in ads)
                    conversion_value = sum(float(ad.get('stat', {}).get('conversion_value', 0)) for ad in ads)

                    results[campaign_name] = {
                        'platform': 'TikTok',
                        'campaign_id': campaign_id,
                        'impressions': impressions,
                        'clicks': clicks,
                        'spend_usd': spend,
                        'conversions': conversions,
                        'conversion_value': conversion_value,
                        'ctr': (clicks / impressions * 100) if impressions > 0 else 0,
                        'cpa': (spend / conversions) if conversions > 0 else 0,
                        'roas': (conversion_value / spend) if spend > 0 else 0,
                    }

            logger.info(f"Fetched {len(results)} TikTok Ads campaigns")
            return results

        except Exception as e:
            logger.error(f"Error fetching TikTok Ads data: {e}")
            return {}


def calculate_pacing(platform: str, spend_mtd: float) -> Tuple[str, float]:
    """
    Calculate pacing status.

    Returns: (status, percentage_diff)
    - AHEAD: spend > budget by >10%
    - ON_PACE: within ±10%
    - BEHIND: spend < budget by >10%
    """
    today = datetime.now(ET)
    days_in_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    days_in_month = days_in_month.day
    day_of_month = today.day

    budget = BUDGET_CONFIG.get(platform, 0)
    if budget == 0:
        return 'UNKNOWN', 0

    expected_spend = (day_of_month / days_in_month) * budget
    percentage_diff = ((spend_mtd - expected_spend) / expected_spend * 100) if expected_spend > 0 else 0

    if percentage_diff > 10:
        status = 'AHEAD'
    elif percentage_diff < -10:
        status = 'BEHIND'
    else:
        status = 'ON_PACE'

    return status, percentage_diff


def consolidate_data(google_data: Dict, meta_data: Dict, tiktok_data: Dict) -> pd.DataFrame:
    """Consolidate data from all platforms."""
    all_campaigns = {}

    for campaign_name, data in google_data.items():
        all_campaigns[f"[Google] {campaign_name}"] = data

    for campaign_name, data in meta_data.items():
        all_campaigns[f"[Meta] {campaign_name}"] = data

    for campaign_name, data in tiktok_data.items():
        all_campaigns[f"[TikTok] {campaign_name}"] = data

    df = pd.DataFrame.from_dict(all_campaigns, orient='index')
    df['date'] = datetime.now(ET).strftime('%Y-%m-%d')
    df['timestamp'] = datetime.now(ET).isoformat()

    return df


def save_to_google_sheets(df: pd.DataFrame, historical_df: pd.DataFrame):
    """Export data to Google Sheets."""
    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON', 'credentials.json'),
            scopes=scope
        )

        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEETS_ID)

        # Update or create "Today" sheet
        try:
            today_sheet = spreadsheet.worksheet('Today')
            today_sheet.clear()
        except:
            today_sheet = spreadsheet.add_worksheet(title='Today', rows=100, cols=20)

        # Convert dataframe to list of lists
        today_sheet.append_rows([df.columns.tolist()] + df.values.tolist())

        # Update or create "Historical" sheet
        try:
            historical_sheet = spreadsheet.worksheet('Historical')
            historical_sheet.clear()
        except:
            historical_sheet = spreadsheet.add_worksheet(title='Historical', rows=1000, cols=20)

        historical_sheet.append_rows([historical_df.columns.tolist()] + historical_df.values.tolist())

        logger.info(f"Exported data to Google Sheets: {GOOGLE_SHEETS_ID}")

    except Exception as e:
        logger.error(f"Error exporting to Google Sheets: {e}")


def save_historical_data(df: pd.DataFrame):
    """Save data to historical CSV file."""
    try:
        if os.path.exists(HISTORICAL_DATA_FILE):
            historical_df = pd.read_csv(HISTORICAL_DATA_FILE)
            historical_df = pd.concat([historical_df, df], ignore_index=True)
        else:
            historical_df = df

        historical_df.to_csv(HISTORICAL_DATA_FILE, index=False)
        logger.info(f"Saved historical data to {HISTORICAL_DATA_FILE}")
        return historical_df

    except Exception as e:
        logger.error(f"Error saving historical data: {e}")
        return df


def generate_dashboard_data(df: pd.DataFrame, historical_df: pd.DataFrame) -> Dict:
    """Generate data for dashboard visualization."""
    dashboard_data = {
        'timestamp': datetime.now(ET).isoformat(),
        'today': {},
        'mtd': {},
        'daily_trends': {},
        'top_campaigns': {},
        'pacing': {},
    }

    # Group by platform
    platforms = df['platform'].unique()

    for platform in platforms:
        platform_data = df[df['platform'] == platform]

        # Today metrics
        dashboard_data['today'][platform] = {
            'spend': platform_data['spend_usd'].sum(),
            'impressions': platform_data['impressions'].sum(),
            'clicks': platform_data['clicks'].sum(),
            'conversions': platform_data['conversions'].sum(),
            'ctr': (platform_data['clicks'].sum() / platform_data['impressions'].sum() * 100) if platform_data['impressions'].sum() > 0 else 0,
            'cpa': (platform_data['spend_usd'].sum() / platform_data['conversions'].sum()) if platform_data['conversions'].sum() > 0 else 0,
            'roas': (platform_data['conversion_value'].sum() / platform_data['spend_usd'].sum()) if platform_data['spend_usd'].sum() > 0 else 0,
        }

        # MTD metrics from historical data
        today = datetime.now(ET).date()
        month_start = today.replace(day=1)

        if not historical_df.empty:
            historical_df['date'] = pd.to_datetime(historical_df['date'])
            mtd_data = historical_df[
                (historical_df['date'] >= pd.Timestamp(month_start)) &
                (historical_df['platform'] == platform)
            ]

            dashboard_data['mtd'][platform] = {
                'spend': mtd_data['spend_usd'].sum(),
                'impressions': mtd_data['impressions'].sum(),
                'clicks': mtd_data['clicks'].sum(),
                'conversions': mtd_data['conversions'].sum(),
                'ctr': (mtd_data['clicks'].sum() / mtd_data['impressions'].sum() * 100) if mtd_data['impressions'].sum() > 0 else 0,
                'cpa': (mtd_data['spend_usd'].sum() / mtd_data['conversions'].sum()) if mtd_data['conversions'].sum() > 0 else 0,
                'roas': (mtd_data['conversion_value'].sum() / mtd_data['spend_usd'].sum()) if mtd_data['spend_usd'].sum() > 0 else 0,
            }
        else:
            dashboard_data['mtd'][platform] = dashboard_data['today'][platform].copy()

        # Pacing status
        status, diff = calculate_pacing(platform, dashboard_data['mtd'][platform]['spend'])
        dashboard_data['pacing'][platform] = {
            'status': status,
            'percentage_diff': round(diff, 2),
            'budget': BUDGET_CONFIG.get(platform, 0),
            'spend_mtd': round(dashboard_data['mtd'][platform]['spend'], 2),
        }

        # Top campaigns
        top_campaigns = platform_data.nlargest(5, 'spend_usd')
        dashboard_data['top_campaigns'][platform] = top_campaigns[
            ['spend_usd', 'impressions', 'clicks', 'conversions', 'cpa', 'roas']
        ].to_dict('records')

        # Daily trends (last 30 days)
        if not historical_df.empty:
            historical_df['date'] = pd.to_datetime(historical_df['date'])
            last_30 = today - timedelta(days=30)
            daily_data = historical_df[
                (historical_df['date'] >= pd.Timestamp(last_30)) &
                (historical_df['platform'] == platform)
            ].groupby('date').agg({
                'spend_usd': 'sum',
                'cpa': 'mean',
            }).reset_index()

            dashboard_data['daily_trends'][platform] = {
                'dates': daily_data['date'].astype(str).tolist(),
                'spend': daily_data['spend_usd'].tolist(),
                'cpa': daily_data['cpa'].tolist(),
            }

    return dashboard_data


def main():
    """Main execution flow."""
    logger.info("Starting data fetch process...")

    # Fetch data from all platforms
    google_fetcher = GoogleAdsDataFetcher()
    meta_fetcher = MetaAdsDataFetcher()
    tiktok_fetcher = TikTokAdsDataFetcher()

    google_data = google_fetcher.fetch_campaigns()
    meta_data = meta_fetcher.fetch_campaigns()
    tiktok_data = tiktok_fetcher.fetch_campaigns()

    # Consolidate data
    df = consolidate_data(google_data, meta_data, tiktok_data)

    # Save historical data
    historical_df = save_historical_data(df)

    # Save to Google Sheets
    save_to_google_sheets(df, historical_df)

    # Generate dashboard data
    dashboard_data = generate_dashboard_data(df, historical_df)

    # Save dashboard data as JSON
    with open('./data/dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=2, default=str)

    logger.info("Data fetch process completed successfully")
    return dashboard_data


if __name__ == '__main__':
    main()
