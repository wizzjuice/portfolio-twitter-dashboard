"""
Weekly Twitter Dashboard for Portfolio Companies
Generates a clean, scannable weekly summary
"""

import requests
import time
import json
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Configuration
API_KEY = "new1_7e7f54a61f99461fa477ad9d9e07f712"
RATE_LIMIT_DELAY = 5
OUTPUT_FILE = "index.html"
DATA_FILE = "last_run.json"

# Load accounts
ACCOUNTS = []
with open("accounts.txt", "r", encoding="utf-8") as f:
    for line in f:
        user = line.strip().lstrip("@").lower()
        if user:
            ACCOUNTS.append(user)

def load_last_run_time():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data["last_run"])
    except:
        return datetime.now(timezone.utc) - timedelta(weeks=1)

def save_last_run_time(run_time):
    with open(DATA_FILE, "w") as f:
        json.dump({"last_run": run_time.isoformat()}, f)

def should_include_tweet(tweet):
    """Simple filter: remove pure retweets, keep everything else"""
    text = tweet.get("text", "")
    return not text.strip().startswith("RT @")

def fetch_tweets_for_account(account, since_str, until_str):
    url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    query = f"from:{account} since:{since_str} until:{until_str}"
    
    params = {"query": query, "queryType": "Latest"}
    headers = {"X-API-Key": API_KEY}
    
    all_tweets = []
    next_cursor = None
    
    while True:
        if next_cursor:
            params["cursor"] = next_cursor
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            tweets = data.get("tweets", [])
            
            if tweets:
                all_tweets.extend(tweets)
            
            if data.get("has_next_page", False) and data.get("next_cursor", ""):
                next_cursor = data.get("next_cursor")
                time.sleep(RATE_LIMIT_DELAY)
                continue
            else:
                break
        else:
            print(f"Error for @{account}: {response.status_code}")
            break
        
        time.sleep(RATE_LIMIT_DELAY)
    
    return all_tweets

def collect_all_data():
    since_time = load_last_run_time()
    until_time = datetime.now(timezone.utc)
    
    since_str = since_time.strftime("%Y-%m-%d_%H:%M:%S_UTC")
    until_str = until_time.strftime("%Y-%m-%d_%H:%M:%S_UTC")
    
    print(f"Collecting tweets from {since_time.date()} to {until_time.date()}")
    print(f"Monitoring {len(ACCOUNTS)} accounts...\n")
    
    all_data = {}
    
    for i, account in enumerate(ACCOUNTS, 1):
        print(f"[{i}/{len(ACCOUNTS)}] @{account}")
        tweets = fetch_tweets_for_account(account, since_str, until_str)
        filtered = [t for t in tweets if should_include_tweet(t)]
        
        if filtered:
            all_data[account] = filtered
            print(f"  ✓ {len(filtered)} tweets")
        else:
            print(f"  - No activity")
        
        if i < len(ACCOUNTS):
            time.sleep(RATE_LIMIT_DELAY)
    
    save_last_run_time(until_time)
    return all_data, since_time, until_time

def generate_html(data, since_time, until_time):
    total_tweets = sum(len(tweets) for tweets in data.values())
    active_accounts = len(data)
    
    # Create summary by account
    account_summaries = []
    for account, tweets in data.items():
        sorted_tweets = sorted(tweets, key=lambda x: x.get('createdAt', ''), reverse=True)
        account_summaries.append({
            'account': account,
            'count': len(tweets),
            'tweets': sorted_tweets
        })
    
    # Sort by tweet count (most active first)
    account_summaries.sort(key=lambda x: x['count'], reverse=True)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Weekly Update</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #1a1a1a;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 50px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #1a1a1a;
        }}
        
        .header .date-range {{
            font-size: 1.1em;
            color: #666;
            margin-bottom: 20px;
        }}
        
        .header .summary {{
            display: inline-flex;
            gap: 30px;
            background: white;
            padding: 20px 40px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .header .summary div {{
            text-align: center;
        }}
        
        .header .summary .number {{
            font-size: 2em;
            font-weight: bold;
            color: #1d9bf0;
        }}
        
        .header .summary .label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .account-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .account-header {{
            display: flex;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        .account-header h2 {{
            font-size: 1.5em;
            color: #1a1a1a;
        }}
        
        .account-header .badge {{
            margin-left: auto;
            background: #1d9bf0;
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }}
        
        .tweet {{
            padding: 20px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .tweet:last-child {{
            border-bottom: none;
        }}
        
        .tweet-date {{
            color: #666;
            font-size: 0.85em;
            margin-bottom: 8px;
        }}
        
        .tweet-text {{
            font-size: 1.05em;
            margin-bottom: 12px;
            line-height: 1.7;
        }}
        
        .tweet-text a {{
            color: #1d9bf0;
            text-decoration: none;
        }}
        
        .tweet-text a:hover {{
            text-decoration: underline;
        }}
        
        .tweet-meta {{
            display: flex;
            gap: 20px;
            color: #666;
            font-size: 0.9em;
            align-items: center;
        }}
        
        .tweet-link {{
            margin-left: auto;
            color: #1d9bf0;
            text-decoration: none;
            font-size: 0.9em;
        }}
        
        .tweet-link:hover {{
            text-decoration: underline;
        }}
        
        .no-activity {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }}
        
        .no-activity h2 {{
            margin-bottom: 10px;
            color: #999;
        }}
        
        @media (max-width: 600px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .header .summary {{
                flex-direction: column;
                gap: 15px;
            }}
            
            .account-card {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Weekly Portfolio Update</h1>
            <div class="date-range">{since_time.strftime('%b %d')} - {until_time.strftime('%b %d, %Y')}</div>
            <div class="summary">
                <div>
                    <div class="number">{active_accounts}</div>
                    <div class="label">Active Companies</div>
                </div>
                <div>
                    <div class="number">{total_tweets}</div>
                    <div class="label">Total Updates</div>
                </div>
            </div>
        </div>
"""
    
    if not account_summaries:
        html += """
        <div class="no-activity">
            <h2>No activity this week</h2>
            <p>None of your portfolio companies posted updates during this period.</p>
        </div>
"""
    else:
        for summary in account_summaries:
            account = summary['account']
            count = summary['count']
            tweets = summary['tweets']
            
            html += f"""
        <div class="account-card">
            <div class="account-header">
                <h2>@{account}</h2>
                <div class="badge">{count} update{'s' if count != 1 else ''}</div>
            </div>
"""
            
            for tweet in tweets:
                text = tweet.get('text', '').replace('\n', '<br>')
                created_at = tweet.get('createdAt', '')
                
                # Parse and format date
                try:
                    dt = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S.%fZ')
                    formatted_date = dt.strftime('%b %d, %I:%M %p')
                except:
                    formatted_date = created_at
                
                likes = tweet.get('favoriteCount', 0)
                retweets = tweet.get('retweetCount', 0)
                replies = tweet.get('replyCount', 0)
                tweet_id = tweet.get('id', '')
                tweet_url = f"https://twitter.com/{account}/status/{tweet_id}"
                
                html += f"""
            <div class="tweet">
                <div class="tweet-date">{formatted_date}</div>
                <div class="tweet-text">{text}</div>
                <div class="tweet-meta">
                    <span>❤️ {likes:,}</span>
                    <span>🔄 {retweets:,}</span>
                    <span>💬 {replies:,}</span>
                    <a href="{tweet_url}" target="_blank" class="tweet-link">View on Twitter →</a>
                </div>
            </div>
"""
            
            html += """
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    return html

def main():
    print("=" * 60)
    print("PORTFOLIO WEEKLY UPDATE GENERATOR")
    print("=" * 60)
    print()
    
    data, since_time, until_time = collect_all_data()
    
    print("\n" + "=" * 60)
    print("GENERATING DASHBOARD")
    print("=" * 60)
    
    html = generate_html(data, since_time, until_time)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n✅ Dashboard generated: {OUTPUT_FILE}")
    print(f"📊 {len(data)} active accounts")
    print(f"📝 {sum(len(t) for t in data.values())} total tweets")

if __name__ == "__main__":
    main()
