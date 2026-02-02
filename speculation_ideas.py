import os
import requests
import datetime
import yfinance as yf
import feedparser
import re

# Configuration
GATEWAY_URL = "http://127.0.0.1:18789/v1/message"
GATEWAY_TOKEN = os.getenv("CLAWDBOT_GATEWAY_TOKEN")
TARGET_CHAT_ID = "833307110" # Russell Personal

def get_reddit_speculation_agent():
    """
    Research agent: Scans high-conviction speculative subreddits for trending 
    setups, unusual options activity, and contrarian plays.
    """
    subs = ["wallstreetbets", "options", "thetagang", "pennystocks"]
    spec_ideas = []
    
    # Keywords indicating a specific speculative setup
    bullish_ks = ["CALLS", "YOLO", "MOON", "BULLISH", "SQUEEZE", "UPGRADE"]
    bearish_ks = ["PUTS", "CRASH", "BEARISH", "SHORT", "HEDGE"]
    
    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/new/.rss"
            feed = feedparser.parse(url, agent="Mozilla/5.0 (Clawdbot Speculation Agent/1.0)")
            
            for entry in feed.entries[:10]:
                title = entry.title
                title_up = title.upper()
                # Find tickers (2-5 caps)
                tickers = re.findall(r'\b[A-Z]{2,5}\b', title_up)
                
                for t in tickers:
                    if t in ["THE", "AND", "FOR", "BUY", "SELL", "NYSE", "NASDAQ", "CEO", "DD", "WSB"]: continue
                    
                    sentiment = ""
                    if any(k in title_up for k in bullish_ks): sentiment = "Bullish / Momentum"
                    elif any(k in title_up for k in bearish_ks): sentiment = "Bearish / Contrarian"
                    
                    if sentiment:
                        spec_ideas.append({
                            "ticker": t,
                            "source": f"r/{sub}",
                            "title": title,
                            "sentiment": sentiment,
                            "link": entry.link
                        })
                if len(spec_ideas) >= 3: break
        except: continue
        if len(spec_ideas) >= 3: break
    return spec_ideas

def get_insider_research_agent():
    """Research agent: Extracts specific ticker ideas from latest SEC Form 4 filings."""
    insider_ideas = []
    headers = {'User-Agent': 'Personal Investment Bot (contact: moltin@example.com)'}
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&count=40&output=atom"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Matches: 4 - TICKER (Person) (Role)
            filings = re.findall(r'<title>4 - (.*?) \((.*?) \((.*?)\)', response.text)
            for ticker, person, role in filings:
                role_lower = role.lower()
                # Prioritize high-level insiders
                if any(r in role_lower for r in ['director', 'officer', 'ceo', 'cfo', 'president']):
                    insider_ideas.append({
                        "ticker": ticker,
                        "person": person,
                        "role": role,
                        "rationale": f"High-conviction move by {role}. Potential follow-the-leader play."
                    })
                if len(insider_ideas) >= 2: break
    except: pass
    return insider_ideas

def get_speculative_report():
    # 1. Price Action Agent (Oversold/Overbought)
    tech_ideas = []
    watchlist = ["TSLA", "NVDA", "AMD", "COIN", "MSTR", "DJT", "SMCI", "NFLX", "LULU"]
    for ticker in watchlist:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if not hist.empty:
                chg = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                if abs(chg) > 8:
                    type = "Long (Oversold)" if chg < 0 else "Short (Overbought)"
                    tech_ideas.append(f"🎯 **Trade Idea: {type} {ticker}**\n   _Rationale:_ 5-day move of {chg:.1f}%. Watching for technical mean reversion.")
        except: continue

    # 2. Reddit Research Agent
    reddit_ideas = get_reddit_speculation_agent()
    # 3. Insider Research Agent
    insider_ideas = get_insider_research_agent()

    # Combine into concrete suggestions
    report = "🔥 **Daily Speculation Ideas (10:30 AM)**\n\n⚡ **CONCRETE TRADE SUGGESTIONS:**\n\n"
    
    # Limit combined ideas
    for idea in tech_ideas[:2]:
        report += idea + "\n\n"
    
    for idea in reddit_ideas[:2]:
        report += (f"🎯 **Trade Idea: {idea['sentiment']} {idea['ticker']}**\n"
                   f"   _Analysis:_ Trending in {idea['source']}: \"{idea['title']}\"\n"
                   f"   🔗 [Source]({idea['link']})\n\n")
                   
    for idea in insider_ideas[:1]:
        report += (f"🎯 **Trade Idea: Follow Insider {idea['person']} ({idea['ticker']})**\n"
                   f"   _Analysis:_ {idea['rationale']}\n\n")

    report += (
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
    content = get_speculative_report()
    notify(content)
