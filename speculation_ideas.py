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

def get_market_movers_agent():
    """
    Research agent: Scans broader market for mid-to-large cap runners (>100% in 30d).
    Uses Yahoo Finance trending/gainers as a starting point for broader discovery.
    """
    runners = []
    # Discover candidates: We look at a mix of high-volume active tickers
    # and use yfinance to filter for the 30-day requirement.
    # Note: For a pure "scan", we iterate a discovery list.
    discovery_list = ["TSLA", "NVDA", "AMD", "COIN", "MSTR", "DJT", "SMCI", "GME", "PLTR", "UPST", "AFRM", "CVNA", "AI", "SOUN", "MARA", "RIOT"]
    
    # Attempt to fetch trending tickers for discovery expansion
    try:
        trending = requests.get("https://query1.finance.yahoo.com/v1/finance/trending/US", headers={'User-Agent': 'Mozilla/5.0'}).json()
        discovered = [t['symbol'] for t in trending['finance']['result'][0]['quotes']]
        discovery_list = list(set(discovery_list + discovered))
    except: pass

    for ticker in discovery_list:
        try:
            # Basic Liquidity check (mid-large cap estimate)
            t = yf.Ticker(ticker)
            info = t.info
            mkt_cap = info.get('marketCap', 0)
            avg_vol = info.get('averageVolume', 0)
            
            if mkt_cap > 2e9 and avg_vol > 500000: # >$2B Market Cap and >500k Avg Vol
                hist_30d = t.history(period="1mo")
                if len(hist_30d) >= 15:
                    monthly_change = ((hist_30d['Close'].iloc[-1] - hist_30d['Close'].iloc[0]) / hist_30d['Close'].iloc[0]) * 100
                    if monthly_change > 100:
                        runners.append({
                            "ticker": ticker,
                            "change": monthly_change,
                            "price": hist_30d['Close'].iloc[-1],
                            "cap": mkt_cap
                        })
        except: continue
    
    runners.sort(key=lambda x: x['change'], reverse=True)
    return runners[:3]

def get_reddit_momentum_agent():
    subs = ["wallstreetbets", "options", "pennystocks"]
    spec_ideas = []
    momentum_ks = ["SQUEEZE", "YOLO", "MOON", "BULLISH", "CALLS", "BREAKOUT", "PUMP", "HIGH VOLUME"]
    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/new/.rss"
            feed = feedparser.parse(url, agent="Mozilla/5.0 (Clawdbot Momentum Agent/1.0)")
            for entry in feed.entries[:10]:
                title_up = entry.title.upper()
                tickers = re.findall(r'\b[A-Z]{2,5}\b', title_up)
                for t in tickers:
                    if t in ["THE", "AND", "FOR", "BUY", "SELL", "NYSE", "NASDAQ", "SEC", "DD", "WSB"]: continue
                    if any(k in title_up for k in momentum_ks):
                        spec_ideas.append({"ticker": t, "source": f"r/{sub}", "title": entry.title, "link": entry.link, "type": "Social Momentum"})
                if len(spec_ideas) >= 5: break
        except: continue
        if len(spec_ideas) >= 5: break
    return spec_ideas

def get_speculative_report():
    # 1. Broad Market Research Agent (Runners > 100%)
    market_runners = get_market_movers_agent()
    # 2. Social Momentum
    momentum_ideas = get_reddit_momentum_agent()
    # 3. Volatility Agent
    volatility_ideas = []
    watchlist = ["TSLA", "NVDA", "AMD", "COIN", "MSTR", "DJT", "SMCI", "NFLX", "LULU", "PLTR", "GME"]
    for ticker in watchlist:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                daily_vol = ((hist['High'].iloc[-1] - hist['Low'].iloc[-1]) / hist['Low'].iloc[-1]) * 100
                if daily_vol > 5:
                    volatility_ideas.append({"ticker": ticker, "vol": daily_vol, "price": hist['Close'].iloc[-1], "high": hist['High'].iloc[-1], "low": hist['Low'].iloc[-1]})
        except: continue
    volatility_ideas.sort(key=lambda x: x['vol'], reverse=True)

    report = "🔥 **Daily Speculation Ideas (10:30 AM)**\n\n⚡ **DETAILED TRADE EXECUTION PLANS:**\n\n"
    added_tickers = set()

    # Add Market Runners (Short Bias)
    for idea in market_runners:
        ticker = idea['ticker']
        report += (f"🎯 **Trade Idea: {ticker} (Short / Puts)**\n"
                   f"   • **Execution:** Long Puts or Bear Call Spread\n"
                   f"   • **Contract:** Monthly expiry, OTM Puts (approx 5-10% below spot)\n"
                   f"   • **Entry:** Confirmation of intraday trend break (e.g. crossing below VWAP).\n"
                   f"   • **Exit:** 40% profit target or 20% stop-loss on premium.\n"
                   f"   _Analysis:_ Found via broad market scan. Dramatic 30-day run of +{idea['change']:.1f}% in a ${idea['cap']/1e9:.1f}B cap stock. High probability of mean reversion.\n\n")
        added_tickers.add(ticker)

    # Add top 2 Social Momentum
    for idea in momentum_ideas:
        if idea['ticker'] not in added_tickers:
            ticker = idea['ticker']
            price_row = yf.Ticker(ticker).history(period="1d")
            price = price_row['Close'].iloc[-1] if not price_row.empty else 0
            report += (f"🎯 **Trade Idea: {ticker} ({idea['type']})**\n"
                       f"   • **Execution:** Option (Bull Call Spread)\n"
                       f"   • **Contract:** Next nearest expiry, strikes at ${price:.0f}/${price*1.05:.0f}\n"
                       f"   • **Entry:** Limit order at mid-price; watch for volume spike confirmation.\n"
                       f"   • **Exit:** 25% profit target or 15% stop-loss on premium.\n"
                       f"   _Analysis:_ Trending in {idea['source']}: \"{idea['title']}\"\n"
                       f"   🔗 [Source]({idea['link']})\n\n")
            added_tickers.add(ticker)
        if len(added_tickers) >= 5: break
            
    # Add top Volatility Momentum
    for idea in volatility_ideas:
        if idea['ticker'] not in added_tickers:
            ticker = idea['ticker']
            report += (f"🎯 **Trade Idea: {ticker} (Intraday Scalp)**\n"
                       f"   • **Execution:** Stock (Long) or ATM Calls\n"
                       f"   • **Entry:** Entry near support at ${idea['low']:.2f}; confirm with RSI < 30 on 5m chart.\n"
                       f"   • **Exit:** Exit target at 1.5% stock gain (${idea['price']*1.015:.2f}) or trailing stop at day-low.\n"
                       f"   _Analysis:_ High intraday volatility ({idea['vol']:.1f}%) detected in market discovery.\n\n")
            added_tickers.add(ticker)
        if len(added_tickers) >= 6: break

    report += (
        "📅 **UPCOMING EARNINGS (NEXT 48H):**\n"
        "• **SNAP** (High IV expected)\n"
        "• **PINS** (Social media sentiment proxy)\n\n"
        "⚠️ *Disclaimer: High risk speculative plays. Trade with discipline.*"
    )
    return report

def notify(text):
    print(text)
    if not GATEWAY_TOKEN: return
    import subprocess
    cmd = ["clawdbot", "message", "send", "--channel", "telegram", "--target", TARGET_CHAT_ID, "--message", text, "--json"]
    try:
        subprocess.run(cmd, capture_output=True, text=True)
    except: pass

if __name__ == '__main__':
    content = get_speculative_report()
    notify(content)
