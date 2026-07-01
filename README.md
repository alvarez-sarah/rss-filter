# Alvarez's NewsFix

A self-hosted, algorithmically curated RSS digest built to filter noise, surface stories that match your interests, and publish a ranked reading list as a shareable webpage three times a day.

**Live digest:** [alvarez-sarah.github.io/rss-filter](https://alvarez-sarah.github.io/rss-filter/)

---

## What this is

Most RSS readers show you everything. This one scores it.

NewsFix pulls articles from a curated list of RSS feeds into a self-hosted Miniflux instance, runs a Python scoring algorithm against a list of interest keywords, balances sources so no single outlet dominates, and publishes the top results as a newspaper-style HTML digest. The page updates automatically at 6am, noon, and 5pm daily via cron.

The algorithm is transparent and forkable. The keyword list and weights are plain Python at the top of score_feeds.py. Anyone can clone this repo, swap in their own interests, and have their own version running in under an hour.

---

## What is in this repo

- docker-compose.yml — Runs Miniflux and Postgres via Docker
- score_feeds.py — Scoring algorithm and HTML digest generator
- deploy.sh — Runs scorer and pushes digest to GitHub Pages
- README.md — This file

---

## How to set it up yourself

### 1. Prerequisites

- Docker Desktop installed and running
- Python 3.9+
- A GitHub account with a repo set up for GitHub Pages

### 2. Clone this repo

    git clone https://github.com/alvarez-sarah/rss-filter.git
    cd rss-filter

### 3. Start Miniflux

    docker compose up -d

Then visit http://localhost:8080 and log in with the credentials in docker-compose.yml. Change the default passwords before using this anywhere public.

### 4. Add your RSS feeds

In Miniflux, click Add Subscription and paste a site URL. Miniflux auto-discovers the feed. Organize feeds into categories under Settings so the algorithm can weight them differently later.

Suggested feeds to start with:

Journalism/Media
- Nieman Lab: https://www.niemanlab.org/feed/
- Press Gazette: https://pressgazette.co.uk/feed/
- Columbia Journalism Review: https://www.cjr.org/feed
- Poynter: https://www.poynter.org/feed/

Tech/AI
- Ars Technica: https://feeds.arstechnica.com/arstechnica/index
- The Verge: https://www.theverge.com/rss/index.xml

Philadelphia
- WHYY: https://whyy.org/feed/
- Billy Penn: https://billypenn.com/feed/
- Philadelphia Inquirer: https://www.inquirer.com/arc/outboundfeeds/rss/

Consumer/Practical
- Wirecutter: https://www.nytimes.com/wirecutter/feed/
- EWG: https://www.ewg.org/news-insights/news
- CPSC Recalls: https://www.cpsc.gov/Newsroom/CPSC-RSS-Feed

Viral/Social
- Reddit Popular: https://reddit.com/r/popular/.rss

### 5. Set up your .env file

Create a file called .env in the project folder with these two lines:

    MINIFLUX_URL=http://localhost:8080
    MINIFLUX_TOKEN=your_api_token_here

Generate your API token in Miniflux under Settings, then API Keys.

### 6. Install Python dependencies

    pip3 install requests python-dotenv

### 7. Customize the algorithm

Open score_feeds.py and edit the INTERESTS list and WEIGHTS dict at the top. These are plain Python, no special syntax needed.

    INTERESTS = [
        "philadelphia city council",
        "big tech regulation",
        "civil rights",
        # add your own
    ]

    WEIGHTS = {
        "philadelphia city council": 3,
        "civil rights": 2,
    }

Two other settings to tune:

- MIN_SCORE: minimum score for an article to appear. Default is 2. Raise to cut noise, lower to see more.
- MAX_PER_FEED: max articles per source in the final output. Default is 3. Keeps one outlet from dominating.

### 8. Test it

    python3 score_feeds.py

This generates index.html in the project folder. Open it in your browser to preview the digest.

### 9. Publish to GitHub Pages

    git add index.html
    git commit -m "Initial digest"
    git push origin main

Then go to your repo on GitHub, click Settings, then Pages, set source to main branch at root, and save. Your digest will be live at https://yourusername.github.io/rss-filter/

### 10. Automate with cron

    crontab -e

Add these three lines to update at 6am, noon, and 5pm daily:

    0 6 * * * cd ~/projects/rss-filter && bash deploy.sh
    0 12 * * * cd ~/projects/rss-filter && bash deploy.sh
    0 17 * * * cd ~/projects/rss-filter && bash deploy.sh

Note: your Mac needs to be awake at these times for cron to run.

---

## How the algorithm works

The scoring pipeline runs in five stages:

1. Fetch: pulls your most recent unread articles from Miniflux via its REST API
2. Score: matches each article title, summary, and content against your INTERESTS list; title matches count double; phrases in WEIGHTS get a multiplier
3. Filter: drops anything below MIN_SCORE
4. Balance: caps each feed at MAX_PER_FEED articles so high-volume sources do not crowd out smaller ones
5. Output: generates a ranked HTML digest and writes it to index.html

This is intentionally simple keyword matching. It is fast, free, and fully transparent. A natural next step is upgrading the scoring to use an LLM API for semantic relevance judgments instead of exact phrase matching.

---

## Built with

- Miniflux: self-hosted RSS reader with a clean API
- Docker: runs Miniflux and Postgres locally
- Python 3: scoring algorithm and HTML generation
- GitHub Pages: free static hosting for the digest

---

## License

MIT. Fork it, adapt it, make it yours.
