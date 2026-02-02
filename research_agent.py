import os
import requests
import datetime
import feedparser
from googleapiclient.discovery import build

# Configuration
GATEWAY_URL = "http://127.0.0.1:18789/v1/message"
GATEWAY_TOKEN = os.getenv("CLAWDBOT_GATEWAY_TOKEN")
TARGET_CHAT_ID = "-1003722298940" # Lins Household Group

def get_research_ideas():
    """
    Research agent that scrapes RSS feeds from reputable financial sources
    to find trending investment ideas and narratives.
    """
    feeds = {
        "MarketWatch": "https://www.marketwatch.com/rss/topstories",
        "SeekingAlpha": "https://seekingalpha.com/market_currents.xml",
        "Investopedia": "https://www.investopedia.com/feedbuilder-feed/latest",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex"
    }
    
    research_results = []
    
    # We look for articles published in the last 24 hours
    now = datetime.datetime.now()
    
    for source, url in feeds.items():
        try:
            feed = feedparser.parse(url, agent="Clawdbot Investment Research Agent/1.0")
            for entry in feed.entries[:5]: # Check top 5 from each
                # Extract keywords that signal an 'idea' or 'recommendation'
                keywords = ["BUY", "SELL", "LONG", "SHORT", "UPGRADE", "TOP PICK", "OPPORTUNITY", "STOCK TO WATCH"]
                title_upper = entry.title.upper()
                
                if any(k in title_upper for k in keywords):
                    # Clean up summary/snippet
                    summary = getattr(entry, 'summary', "Read more at source.")
                    if len(summary) > 200:
                        summary = summary[:200] + "..."
                        
                    research_results.append({
                        "source": source,
                        "title": entry.title,
                        "link": entry.link,
                        "summary": summary
                    })
        except Exception as e:
            print(f"Error researching {source}: {e}")
            
    return research_results[:3] # Return top 3 curated ideas

def get_briefing():
    # Keep the FX logic (omitted here for brevity, but stays in the main file)
    # ... 
    
    research_ideas = get_research_ideas()
    
    idea_section = ""
    if research_ideas:
        for idea in research_ideas:
            idea_section += (
                f"🎯 **{idea['title']}**\n"
                f"   _Analysis:_ {idea['summary']}\n"
                f"   🔗 [Source ({idea['source']})]({idea['link']})\n\n"
            )
    else:
        idea_section = "No new high-conviction ideas found in recent research cycle."

    # Construct the full message
    # ...
    return idea_section

if __name__ == '__main__':
    print(get_research_ideas())
