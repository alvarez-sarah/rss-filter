#!/usr/bin/env python3
"""
Alvarez's NewsFix - RSS Feed Scorer
Fetches, scores, and publishes a ranked digest as HTML.
"""

import os
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
import requests

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

INTERESTS = [
    # Philadelphia
    "philadelphia neighborhood development",
    "neighborhood development",
    "philadelphia city council",
    "philadelphia",
    "philly",

    # Detroit
    "detroit",
    "detroiters",

    # Big tech
    "big tech abuses of power",
    "big tech regulation",
    "lawsuits against big tech",
    "investigations into big tech",
    "antitrust",
    "tech accountability",

    # Sports betting
    "investigations into sports betting",
    "sports betting",

    # Cycling
    "world tour cycling",
    "tour de france",
    "cycling",
    "pro cycling",

    # Books
    "book review",
    "book reviews",
    "new book",

    # Social/protest/civil rights
    "protests",
    "protest",
    "civil rights",
    "civil liberties",

    # Viral content
    "viral",
    "trending",
    "going viral",

    # News you can use / practical consumer advice
    "news you can use",
    "what you need to know",
    "explainer",
    "guide to",

    # Shopping / best of / editor's picks
    "editor's picks",
    "editors picks",
    "best of",
    "shopping guide",
    "gift guide",
    "beauty picks",
    "style guide",
    "best dressed",
    "outfit ideas",

    # Consumer safety / harmful ingredients
    "harmful ingredients",
    "ingredients to avoid",
    "consumer warning",
    "health warning",
    "hidden dangers",
    "consumer alert",
    "FDA warning",
    "recall",
    "PFAS",
    "forever chemicals",
    "toxic chemicals",
    "fragrance in skincare",
    "clean beauty",
    "skin deep",
]

WEIGHTS = {
    "philadelphia neighborhood development": 3,
    "philadelphia city council": 3,
    "big tech abuses of power": 3,
    "investigations into big tech": 3,
    "investigations into sports betting": 3,
    "world tour cycling": 3,
    "civil rights": 2,
    "protests": 2,
    "detroit": 2,
    "book review": 2,
    "antitrust": 2,
    "recall": 2,
    "FDA warning": 2,
    "PFAS": 2,
}

MIN_SCORE = 2
MAX_PER_FEED = 3
TOP_N = 30
FETCH_LIMIT = 200


# ─────────────────────────────────────────────
# FETCH
# ─────────────────────────────────────────────

def fetch_unread(base_url, token, limit=FETCH_LIMIT):
    url = base_url + "/v1/entries"
    headers = {"X-Auth-Token": token}
    params = {"status": "unread", "limit": limit, "order": "published_at", "direction": "desc"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get("entries", [])


# ─────────────────────────────────────────────
# SCORE
# ─────────────────────────────────────────────

def score_article(entry):
    title = (entry.get("title") or "").lower()
    content = (entry.get("content") or "").lower()
    summary = (entry.get("summary") or "").lower()
    feed_title = (entry.get("feed", {}).get("title") or "").lower()
    searchable = title + " " + title + " " + summary + " " + content + " " + feed_title
    score = 0
    matched = []
    for phrase in INTERESTS:
        if phrase.lower() in searchable:
            weight = WEIGHTS.get(phrase, 1)
            score += weight
            matched.append(phrase)
    return score, list(set(matched))


# ─────────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────────

def filter_articles(entries, min_score=MIN_SCORE):
    scored = []
    for entry in entries:
        score, matched = score_article(entry)
        if score >= min_score:
            scored.append((score, matched, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


# ─────────────────────────────────────────────
# BALANCE
# ─────────────────────────────────────────────

def balance_sources(scored_entries, max_per_feed=MAX_PER_FEED, top_n=TOP_N):
    feed_counts = defaultdict(int)
    balanced = []
    for score, matched, entry in scored_entries:
        feed_id = entry.get("feed", {}).get("id", "unknown")
        if feed_counts[feed_id] < max_per_feed:
            balanced.append((score, matched, entry))
            feed_counts[feed_id] += 1
        if len(balanced) >= top_n:
            break
    return balanced


# ─────────────────────────────────────────────
# HTML OUTPUT
# ─────────────────────────────────────────────

def category_label(matched):
    """Return a category badge label based on matched keywords."""
    cats = {
        "philadelphia": "Philadelphia",
        "philly": "Philadelphia",
        "philadelphia city council": "Philadelphia",
        "philadelphia neighborhood development": "Philadelphia",
        "detroit": "Detroit",
        "antitrust": "Big Tech",
        "big tech": "Big Tech",
        "tech accountability": "Big Tech",
        "civil rights": "Civil Rights",
        "protests": "Civil Rights",
        "protest": "Civil Rights",
        "cycling": "Cycling",
        "tour de france": "Cycling",
        "world tour cycling": "Cycling",
        "book review": "Books",
        "book reviews": "Books",
        "recall": "Consumer Safety",
        "FDA warning": "Consumer Safety",
        "harmful ingredients": "Consumer Safety",
        "PFAS": "Consumer Safety",
        "forever chemicals": "Consumer Safety",
        "sports betting": "Sports Betting",
        "viral": "Trending",
        "trending": "Trending",
        "editor's picks": "Best Of",
        "editors picks": "Best Of",
        "best of": "Best Of",
        "explainer": "Explainer",
        "what you need to know": "Explainer",
        "news you can use": "News You Can Use",
    }
    for phrase in matched:
        if phrase.lower() in cats:
            return cats[phrase.lower()]
    return "General"

def build_html(balanced_entries, updated_at):
    articles_html = ""
    for rank, (score, matched, entry) in enumerate(balanced_entries, 1):
        title = entry.get("title", "No title")
        url = entry.get("url", "#")
        feed_title = entry.get("feed", {}).get("title", "Unknown")
        published = entry.get("published_at", "")[:10]
        category = category_label(matched)
        tags = ", ".join(sorted(set(matched)))

        articles_html += f"""
        <article class="story">
            <div class="story-meta">
                <span class="rank">#{rank}</span>
                <span class="category">{category}</span>
                <span class="source">{feed_title}</span>
                <span class="date">{published}</span>
            </div>
            <h2 class="headline"><a href="{url}" target="_blank">{title}</a></h2>
            <div class="tags">Matched: {tags}</div>
        </article>
        """

    empty = ""
    if not balanced_entries:
        empty = '<p class="empty">No articles matched your interests yet. Check back after feeds update.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alvarez's NewsFix</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --ink: #1A1410;
            --paper: #F6F1E7;
            --rule: #1A1410;
            --accent: #B5261E;
            --muted: #6B6560;
            --tag-bg: #1A1410;
            --tag-text: #F6F1E7;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            background: var(--paper);
            color: var(--ink);
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 18px;
            line-height: 1.6;
        }}

        /* MASTHEAD */
        .masthead {{
            border-top: 6px solid var(--rule);
            border-bottom: 3px solid var(--rule);
            padding: 1.5rem 0 1rem;
            text-align: center;
            margin-bottom: 0;
        }}

        .masthead-eyebrow {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 0.4rem;
        }}

        .masthead h1 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: clamp(2.8rem, 8vw, 5.5rem);
            font-weight: 900;
            letter-spacing: -0.02em;
            line-height: 1;
            color: var(--ink);
        }}

        .masthead-rule {{
            border: none;
            border-top: 1px solid var(--rule);
            margin: 0.8rem auto 0.5rem;
            width: 80%;
        }}

        .masthead-dateline {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 0.1em;
            color: var(--muted);
        }}

        /* SUBHEAD BAR */
        .subhead-bar {{
            background: var(--ink);
            color: var(--paper);
            text-align: center;
            padding: 0.45rem 1rem;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}

        /* MAIN CONTENT */
        .container {{
            max-width: 860px;
            margin: 0 auto;
            padding: 0 1.5rem 4rem;
        }}

        .section-label {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.65rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: var(--muted);
            border-bottom: 1px solid var(--rule);
            padding: 2rem 0 0.4rem;
            margin-bottom: 0;
        }}

        /* STORY */
        .story {{
            border-bottom: 1px solid #C8C2B5;
            padding: 1.4rem 0;
        }}

        .story:last-child {{
            border-bottom: none;
        }}

        .story-meta {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            flex-wrap: wrap;
            margin-bottom: 0.5rem;
        }}

        .rank {{
            font-family: 'Playfair Display', serif;
            font-size: 0.85rem;
            font-weight: 700;
            background: var(--accent);
            color: #fff;
            padding: 0.05rem 0.4rem;
            min-width: 2rem;
            text-align: center;
        }}

        .category {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.65rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            background: var(--tag-bg);
            color: var(--tag-text);
            padding: 0.15rem 0.5rem;
        }}

        .source {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.68rem;
            color: var(--muted);
            letter-spacing: 0.05em;
        }}

        .date {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.65rem;
            color: var(--muted);
            margin-left: auto;
        }}

        .headline {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: clamp(1.1rem, 2.5vw, 1.45rem);
            font-weight: 700;
            line-height: 1.25;
            margin-bottom: 0.4rem;
        }}

        .headline a {{
            color: var(--ink);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.15s;
        }}

        .headline a:hover {{
            border-bottom-color: var(--accent);
            color: var(--accent);
        }}

        .tags {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.62rem;
            color: var(--muted);
            letter-spacing: 0.04em;
        }}

        .empty {{
            text-align: center;
            color: var(--muted);
            font-style: italic;
            padding: 3rem 0;
        }}

        /* FOOTER */
        .footer {{
            border-top: 3px solid var(--rule);
            margin-top: 3rem;
            padding: 1.2rem 0;
            text-align: center;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.65rem;
            letter-spacing: 0.1em;
            color: var(--muted);
        }}

        @media (max-width: 600px) {{
            .date {{ margin-left: 0; }}
        }}
    </style>
</head>
<body>
    <header class="masthead">
        <p class="masthead-eyebrow">A curated digest by Sara Alvarez</p>
        <h1>Alvarez's NewsFix</h1>
        <hr class="masthead-rule">
        <p class="masthead-dateline">Updated {updated_at} &nbsp;·&nbsp; {len(balanced_entries)} stories ranked by relevance</p>
    </header>

    <div class="subhead-bar">Philadelphia &nbsp;·&nbsp; Big Tech &nbsp;·&nbsp; Civil Rights &nbsp;·&nbsp; Detroit &nbsp;·&nbsp; Consumer Safety &nbsp;·&nbsp; And More</div>

    <main class="container">
        <p class="section-label">Today's Ranked Stories</p>
        {articles_html}
        {empty}
    </main>

    <footer class="footer">
        Alvarez's NewsFix &nbsp;·&nbsp; Powered by Miniflux &amp; a custom scoring algorithm &nbsp;·&nbsp; <a href="https://github.com/alvarez-sarah/rss-filter" style="color:inherit">View source on GitHub</a>
    </footer>
</body>
</html>"""


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    load_dotenv()
    base_url = os.getenv("MINIFLUX_URL", "").rstrip("/")
    token = os.getenv("MINIFLUX_TOKEN", "")

    if not base_url or not token:
        print("Missing MINIFLUX_URL or MINIFLUX_TOKEN in your .env file.")
        return

    print("Fetching articles from " + base_url + "...")
    entries = fetch_unread(base_url, token)
    print("Fetched " + str(len(entries)) + " articles.")

    scored = filter_articles(entries)
    print(str(len(scored)) + " articles matched.")

    balanced = balance_sources(scored)

    updated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    html = build_html(balanced, updated_at)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(output_path, "w") as f:
        f.write(html)

    print("Digest written to " + output_path)

if __name__ == "__main__":
    main()
