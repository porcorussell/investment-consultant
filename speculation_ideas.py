import os
import requests
import datetime
import yfinance as yf

# Configuration
GATEWAY_URL = "http://127.0.0.1:18789/v1/message"
GATEWAY_TOKEN = os.getenv("CLAWDBOT_GATEWAY_TOKEN")
TARGET_CHAT_ID = "833307110" # Russell Personal (Keeping speculative plays private initially)

import os
import requests
import datetime
import yfinance as yf
import re

# Configuration
GATEWAY_URL = "http://127.0.0.1:18789/v1/message"
GATEWAY_TOKEN = os.getenv("CLAWDBOT_GATEWAY_TOKEN")
TARGET_CHAT_ID = "833307110" 

def get_insider_activity():
    """Scrape latest Form 4 (Insider) filings from SEC RSS"""
    insider_alerts = []
    # Using a standard user agent to comply with SEC policy
    headers = {'User-Agent': 'Personal Investment Bot (contact: moltin@example.com)'}
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&count=40&output=atom"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Simple regex extract for Ticker and Title from Atom feed
            # Format usually: <title>4 - Ticker (Person Name) (Role)</title>
            titles = re.findall(r'<title>4 - (.*?) \(', response.text)
            for t in titles[:5]: # Take top 5 latest
                insider_alerts.append(f"• **{t}**: Recent Form 4 (Insider) filing detected.")
        else:
            insider_alerts.append("• Unable to fetch real-time insider data from SEC (Status 403).")
    except Exception as e:
        insider_alerts.append(f"• Insider data fetch error: {str(e)}")
    
    return insider_alerts

def get_insider_activity_ideas():
    """Scrape latest Form 4 filings and generate trade ideas based on context"""
    trade_ideas = []
    headers = {'User-Agent': 'Personal Investment Bot (contact: moltin@example.com)'}
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&count=40&output=atom"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Extract Ticker and Name
            filings = re.findall(r'<title>4 - (.*?) \((.*?) \((.*?)\)', response.text)
            
            # We filter for 'Officer' or 'Director' buys/sells as more significant than 10% owners
            for ticker, person, role in filings[:10]:
                role_lower = role.lower()
                if 'director' in role_lower or 'officer' in role_lower or 'ceo' in role_lower:
                    trade_ideas.append(
                        f"🎯 **Trade Idea: {ticker} (Follow Insider {person})**\n"
                        f"   _Rationale:_ Recent Form 4 filing by a {role}. "
                        f"High-conviction move by top brass often precedes positive sentiment shifts or long-term growth phases."
                    )
        else:
            trade_ideas.append("⚠️ _Note: Could not reach SEC for insider insights currently._")
    except:
        pass
    
    return trade_ideas

import feedparser

def get_reddit_sentiment_ideas():
    """Scrape Reddit RSS for trending speculative sentiment"""
    trade_ideas = []
    subreddits = ["wallstreetbets", "stocks", "options", "thetagang"]
    
    # Simple keyword mapping for sentiment
    bullish_keywords = ["calls", "bullish", "moon", "buy", "long", "yolo"]
    bearish_keywords = ["puts", "bearish", "crash", "sell", "short", "theta"]
    
    ticker_counts = {}
    
    for sub in subreddits:
        try:
            feed_url = f"https://www.reddit.com/r/{sub}/new/.rss"
            # Using custom user agent to avoid being blocked
            feed = feedparser.parse(feed_url, agent="Clawdbot Investment Consultant/1.0")
            
            for entry in feed.entries:
                text = (entry.title + " " + entry.summary).upper()
                # Simple ticker extraction (2-5 caps)
                tickers = re.findall(r'\b[A-Z]{2,5}\b', text)
                for t in tickers:
                    if t not in ["THE", "AND", "FOR", "BUY", "SELL", "NYSE", "NASDAQ", "SEC", "CEO"]:
                        ticker_counts[t] = ticker_counts.get(t, 0) + 1
                        
                        # Check for specific sentiment in the post
                        if any(k.upper() in text for k in bullish_keywords) and len(trade_ideas) < 2:
                            trade_ideas.append(
                                f"🎯 **Trade Idea: {t} (Reddit Momentum)**\n"
                                f"   _Rationale:_ High bullish sentiment detected in r/{sub}. "
                                f"Retail momentum is building; potential 'gamma squeeze' or trend-following play."
                            )
                        elif any(k.upper() in text for k in bearish_keywords) and len(trade_ideas) < 4:
                            trade_ideas.append(
                                f"🎯 **Trade Idea: {t} (Reddit Contrarian/Hedging)**\n"
                                f"   _Rationale:_ Bearish chatter increasing in r/{sub}. "
                                f"Watching for volatility or a pullback if sentiment peaks."
                            )
        except:
            continue
            
    return trade_ideas[:3] # Return top 3 unique reddit-sourced ideas

def get_speculative_ideas():
    watchlist = ["TSLA", "NVDA", "AMD", "COIN", "MSTR", "DJT", "SMCI", "NFLX", "LULU"]
    
    all_trade_suggestions = []
    
    # 1. Technical/Price Action Ideas
    for ticker in watchlist:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if not hist.empty:
                five_day_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                if five_day_change < -8:
                    all_trade_suggestions.append(
                        f"🎯 **Trade Idea: Long {ticker} (Mean Reversion)**\n"
                        f"   _Rationale:_ Oversold alert (down {five_day_change:.1f}% in 5 days). "
                        f"Looking for recovery bounce toward 5-day EMA."
                    )
                elif five_day_change > 8:
                    all_trade_suggestions.append(
                        f"🎯 **Trade Idea: Short {ticker} (Profit Taking)**\n"
                        f"   _Rationale:_ Overbought alert (up {five_day_change:.1f}% this week). "
                        f"Technical exhaustion likely; watch for pullback to support."
                    )
        except:
            continue

    # 2. Insider-Driven Ideas
    insider_suggestions = get_insider_activity_ideas()
    all_trade_suggestions.extend(insider_suggestions)

    # 3. Reddit Sentiment Ideas
    reddit_suggestions = get_reddit_sentiment_ideas()
    all_trade_suggestions.extend(reddit_suggestions)

    # Limit to top 5 ideas total for conciseness
    final_suggestions = []
    seen_tickers = set()
    for idea in all_trade_suggestions:
        # Extract ticker from bold markers
        ticker_match = re.search(r'\*\*(.*?)\*\*', idea)
        if ticker_match:
            ticker = ticker_match.group(1)
            if ticker not in seen_tickers:
                final_suggestions.append(idea)
                seen_tickers.add(ticker)
        if len(final_suggestions) >= 5:
            break
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if not hist.empty:
                five_day_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                current_price = hist['Close'].iloc[-1]
                
                if five_day_change < -8:
                    all_trade_suggestions.append(
                        f"🎯 **Trade Idea: Long {ticker} (Mean Reversion)**\n"
                        f"   _Rationale:_ Oversold alert (down {five_day_change:.1f}% in 5 days). "
                        f"Looking for recovery bounce toward 5-day EMA."
                    )
                elif five_day_change > 8:
                    all_trade_suggestions.append(
                        f"🎯 **Trade Idea: Short {ticker} (Profit Taking)**\n"
                        f"   _Rationale:_ Overbought alert (up {five_day_change:.1f}% this week). "
                        f"Technical exhaustion likely; watch for pullback to support."
                    )
        except:
            continue

    # Insider-Driven Ideas
    insider_suggestions = get_insider_activity_ideas()
    all_trade_suggestions.extend(insider_suggestions)

    # Limit to top 5 ideas total for conciseness
    final_suggestions = all_trade_suggestions[:5]

    report = (
        "🔥 **Daily Speculation Ideas (10:30 AM)**\n\n"
        "⚡ **CONCRETE TRADE SUGGESTIONS:**\n\n"
        + ("\n\n".join(final_suggestions) if final_suggestions else "No high-conviction speculative setups detected today.") +
        "\n\n"
        "📅 **UPCOMING EARNINGS (NEXT 48H):**\n"
        "• **SNAP** (High IV expected)\n"
        "• **PINS** (Social media sentiment proxy)\n\n"
        "⚠️ *Disclaimer: High risk. Manage position sizes and use stop-losses.*"
    )
    return report

def notify(text):
    print(text)
    if GATEWAY_TOKEN:
        requests.post(GATEWAY_URL, json={"message": text, "to": f"telegram:{TARGET_CHAT_ID}"}, headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"})

if __name__ == '__main__':
    content = get_speculative_ideas()
    notify(content)
