# Pei Wei Ads Performance Dashboard

Automated system for tracking ad spend pacing and performance metrics across Google Ads, Meta Ads, and TikTok Ads. Generates daily performance reports with pacing alerts and trend analysis.

## Features

✅ **Real-time Pacing Tracking** - Monitor spend against June budget with status alerts (On Pace, Ahead, Behind)  
✅ **Multi-Platform Integration** - Fetch metrics from Google Ads, Meta Ads, and TikTok Ads  
✅ **Historical Data** - Maintains 30-day history for trend analysis  
✅ **Automated Reports** - Runs daily at 7:00 AM ET, exports to Google Sheets  
✅ **Interactive Dashboard** - Standalone HTML with Chart.js visualizations  
✅ **GitHub Pages Hosting** - Auto-deployed with each update  

## Budget Configuration (June)

| Channel | Budget | % of Total |
|---------|--------|-----------|
| Google Search | $18,600 | 28% |
| Google PMax | $25,200 | 38% |
| Meta Ads | $19,300 | 29% |
| TikTok | $1,900 | 3% |
| Apple | $675 | 1% |
| Google App Campaigns | $675 | 1% |
| **Total** | **$66,350** | **100%** |

## Setup Instructions

### 1. Local Environment Setup

```bash
# Clone the repository
git clone https://github.com/topobenquet/peiwei-dashboard.git
cd peiwei-dashboard

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env template and fill with credentials
cp .env.example .env
```

### 2. API Credentials Setup

#### Google Ads API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google Ads API
4. Create OAuth 2.0 credentials (Desktop app):
   - Application type: Desktop
   - Download JSON file
5. Set environment variables:
   ```
   GOOGLE_ADS_DEVELOPER_TOKEN=<your_token>
   GOOGLE_ADS_CUSTOMER_ID=934-886-7971
   GOOGLE_ADS_CLIENT_ID=<from_json>
   GOOGLE_ADS_CLIENT_SECRET=<from_json>
   GOOGLE_ADS_REFRESH_TOKEN=<generate_via_oauth_flow>
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=934-886-7971
   ```

#### Meta Ads API
1. Go to [Meta for Developers](https://developers.facebook.com)
2. Create app and select "Marketing API"
3. Get your credentials:
   ```
   META_APP_ID=<app_id>
   META_APP_SECRET=<app_secret>
   META_ACCESS_TOKEN=<generate_token>
   META_AD_ACCOUNT_ID=242286109226006
   ```
4. Test connection:
   ```bash
   python -c "from facebook_business.api import FacebookAdsApi; FacebookAdsApi.init(access_token='YOUR_TOKEN')"
   ```

#### TikTok Ads API
1. Go to [TikTok for Business](https://business.tiktok.com/en/apps)
2. Create app for TikTok Marketing API
3. Get credentials:
   ```
   TIKTOK_APP_ID=<app_id>
   TIKTOK_APP_SECRET=<app_secret>
   TIKTOK_ACCESS_TOKEN=<generate_token>
   TIKTOK_ADVERTISER_ID=7099894550273081346
   TIKTOK_REDIRECT_URI=https://jbenquet.com
   ```

#### Google Sheets API
1. In Google Cloud Console, enable Google Sheets API
2. Create Service Account credentials:
   - Service account > Create key > JSON
   - Download JSON file
3. Share Google Sheet with service account email (from JSON)
4. Set in .env:
   ```
   GOOGLE_SHEETS_ID=1MUolDzzAvBpkvD1pRSROFRffKh9d5UUGm0JPCwyWWrs
   GOOGLE_SHEETS_CREDENTIALS_JSON=credentials.json
   ```

### 3. Test Locally

```bash
# Ensure .env file is filled with all credentials
python fetch_data.py

# Check output
ls -la data/
cat data/dashboard_data.json
```

### 4. GitHub Setup

#### Create GitHub Secrets

Add these secrets to your repository (Settings > Secrets and variables > Actions):

```
META_APP_ID
META_APP_SECRET
META_ACCESS_TOKEN
META_AD_ACCOUNT_ID
TIKTOK_APP_ID
TIKTOK_APP_SECRET
TIKTOK_ACCESS_TOKEN
TIKTOK_ADVERTISER_ID
TIKTOK_REDIRECT_URI
GOOGLE_ADS_DEVELOPER_TOKEN
GOOGLE_ADS_CUSTOMER_ID
GOOGLE_ADS_CLIENT_ID
GOOGLE_ADS_CLIENT_SECRET
GOOGLE_ADS_REFRESH_TOKEN
GOOGLE_ADS_LOGIN_CUSTOMER_ID
GOOGLE_SHEETS_ID
GOOGLE_SHEETS_CREDENTIALS
GEMINI_API_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
```

**Important**: For `GOOGLE_SHEETS_CREDENTIALS`, paste the entire JSON content as a secret (one line, no formatting).

#### Enable GitHub Pages

1. Go to repository Settings > Pages
2. Set source to "Deploy from a branch"
3. Select `main` branch (or `gh-pages` after first deploy)
4. Optionally set custom domain

#### Configure Workflow

The workflow file (`.github/workflows/update_dashboard.yml`) is pre-configured to:
- Run daily at 7:00 AM ET (11:00 UTC)
- Allow manual trigger via "Run workflow" button
- Auto-deploy to GitHub Pages

## Running the Dashboard

### Local
```bash
# Start a local server
python -m http.server 8000

# Visit http://localhost:8000/dashboard.html
```

### GitHub Pages
Dashboard will be available at:
- `https://github.com/topobenquet/peiwei-dashboard` (repository)
- Auto-deployed URL after setting custom domain
- Default: `https://topobenquet.github.io/peiwei-dashboard/dashboard.html`

## Dashboard Sections

### 1. Pacing Status
Visual cards showing:
- Monthly budget vs current spend
- % of budget executed
- Status badge (AHEAD, ON_PACE, BEHIND)
- Progress bar with variance indicator

**Thresholds**:
- ✅ **ON_PACE**: Within ±10% of expected spend
- ⚠️ **AHEAD**: >10% over expected spend
- 🔴 **BEHIND**: >10% under expected spend

### 2. Performance Metrics
Two tables showing:
- **Previous Day**: Yesterday's metrics
- **Month-to-Date**: Cumulative June metrics

Columns: Spend, Impressions, Clicks, CTR, Conversions, CPA, ROAS

### 3. 30-Day Trends
Line charts for:
- **Daily Spend** by platform
- **Daily CPA** (Cost Per Acquisition) trends

### 4. Top Campaigns
Top 5 campaigns per platform by spend with metrics:
- Impressions, Clicks, Conversions
- CPA, ROAS

## File Structure

```
peiwei-dashboard/
├── .github/
│   └── workflows/
│       └── update_dashboard.yml        # GitHub Actions workflow
├── data/
│   ├── dashboard_data.json            # Latest dashboard data
│   └── historical_data.csv            # 30+ days historical data
├── fetch_data.py                       # Main data fetching script
├── dashboard.html                      # Standalone dashboard
├── requirements.txt                    # Python dependencies
├── .env                               # Local environment (git ignored)
├── .env.example                       # Environment template
└── README.md                          # This file
```

## Troubleshooting

### "Failed to initialize Google Ads client"
- Ensure `google-ads-python` is installed: `pip install google-ads`
- Verify OAuth credentials are valid in `.env`
- Check developer token is activated in Google Ads account

### "Dashboard data not loading"
- Ensure `fetch_data.py` has been run: `python fetch_data.py`
- Check `data/dashboard_data.json` exists and has content
- Refresh browser and clear cache

### "GitHub Actions workflow fails"
1. Check action logs: GitHub > Actions > Update Ads Dashboard
2. Verify all secrets are set correctly
3. Ensure credentials JSON is properly formatted (one line)
4. Check API tokens haven't expired

### "No data from [Platform]"
1. Test API connection locally: `python fetch_data.py`
2. Check credentials in `.env` are correct
3. Verify API token permissions (scopes)
4. Check if account/advertiser IDs are correct:
   - Google Ads: 934-886-7971
   - Meta Ads: 242286109226006
   - TikTok: 7099894550273081346

## Customization

### Change Schedule
Edit `.github/workflows/update_dashboard.yml`:
```yaml
cron: '0 11 * * *'  # Change to desired time (UTC)
```

### Update Budget
Edit `fetch_data.py` in `BUDGET_CONFIG`:
```python
BUDGET_CONFIG = {
    'Google Search': 18600,
    'Google PMax': 25200,
    'Meta Ads': 19300,
    'TikTok': 1900,
}
```

### Change Dashboard Colors
Edit `dashboard.html` CSS:
```css
.header {
    background: linear-gradient(135deg, #E63946 0%, #c41235 100%);
}
```

## Dependencies

- `google-ads` - Google Ads API client
- `facebook-business` - Meta Ads API client
- `requests` - HTTP library for TikTok API
- `gspread` - Google Sheets API client
- `pandas` - Data manipulation
- `python-dotenv` - Environment variable management
- `pytz` - Timezone handling

See `requirements.txt` for pinned versions.

## Performance Notes

- Dashboard auto-reloads every 5 minutes
- Historical data maintained in CSV (append-only)
- Charts render client-side for best performance
- No server required (static HTML + JSON)

## Security

⚠️ **Important**:
- Never commit `.env` file (already in `.gitignore`)
- Use GitHub Secrets for all credentials
- Rotate API tokens periodically
- Review access logs for leaked credentials

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review GitHub Actions logs
3. Verify all API credentials and permissions
4. Check `fetch_data.py` for error messages (enable DEBUG logging if needed)

---

**Last Updated**: June 2026  
**Timezone**: Eastern (ET)  
**Schedule**: Daily at 7:00 AM ET  
**Dashboard**: https://peiwei-ads-dashboard.jbenquet.com
