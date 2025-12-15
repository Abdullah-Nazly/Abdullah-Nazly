#!/usr/bin/env python3
"""
Generate custom GitHub stats SVG with enhanced features
"""
import os
from collections import defaultdict
from datetime import datetime, timedelta

import requests

# Configuration
USERNAME = "Abdullah-Nazly"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
THEME = {
    "bg": "#0d1117",
    "bg_secondary": "#161b22",
    "text": "#c9d1d9",
    "text_secondary": "#8b949e",
    "accent": "#58a6ff",
    "accent_secondary": "#79c0ff",
    "success": "#3fb950",
    "warning": "#d29922",
    "border": "#30363d",
    "icon": "#7c3aed",
    "gradient_start": "#58a6ff",
    "gradient_end": "#bc8cff",
}


def get_contribution_streak(headers):
    """Calculate contribution streaks from events"""
    # Get user events to calculate streaks
    events_url = f"https://api.github.com/users/{USERNAME}/events/public?per_page=100"
    events_response = requests.get(events_url, headers=headers)
    events = events_response.json()

    # Handle API errors
    if not isinstance(events, list):
        return {"current": 0, "longest": 0}

    # Get contribution dates
    contribution_dates = set()
    for event in events:
        if isinstance(event, dict) and event.get("type") in [
            "PushEvent",
            "PullRequestEvent",
            "IssuesEvent",
            "CreateEvent",
        ]:
            date_str = event.get("created_at", "")[:10]  # YYYY-MM-DD
            if date_str:
                contribution_dates.add(date_str)

    # Calculate streaks
    today = datetime.now().date()
    dates = sorted(
        [datetime.strptime(d, "%Y-%m-%d").date() for d in contribution_dates if d]
    )

    if not dates:
        return {"current": 0, "longest": 0}

    # Current streak
    current_streak = 0
    check_date = today
    while check_date in dates or check_date == today:
        if check_date in dates:
            current_streak += 1
        check_date -= timedelta(days=1)

    # Longest streak
    longest_streak = 1
    max_streak = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            max_streak += 1
        else:
            longest_streak = max(longest_streak, max_streak)
            max_streak = 1
    longest_streak = max(longest_streak, max_streak)

    return {"current": current_streak, "longest": longest_streak}


def get_github_stats():
    """Fetch comprehensive stats from GitHub API"""
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # Get user info
    user_url = f"https://api.github.com/users/{USERNAME}"
    user_data = requests.get(user_url, headers=headers).json()

    # Get repos
    repos_url = f"https://api.github.com/users/{USERNAME}/repos?type=all&per_page=100"
    repos_response = requests.get(repos_url, headers=headers)
    repos_data = repos_response.json()

    # Handle API errors
    if not isinstance(repos_data, list):
        print(f"Warning: Repos API returned non-list: {repos_data}")
        repos_data = []

    # Calculate basic stats
    if not repos_data:
        repos_data = []
    total_repos = len(repos_data)
    public_repos = [
        r for r in repos_data if isinstance(r, dict) and not r.get("private", False)
    ]
    private_repos = total_repos - len(public_repos)
    total_stars = sum(
        repo.get("stargazers_count", 0) for repo in repos_data if isinstance(repo, dict)
    )
    total_forks = sum(
        repo.get("forks_count", 0) for repo in repos_data if isinstance(repo, dict)
    )

    # Get contributions and calculate streaks
    streaks = get_contribution_streak(headers)

    # Language stats with percentages
    languages = defaultdict(int)
    total_bytes = 0

    for repo in public_repos:
        lang_url = repo.get("languages_url")
        if lang_url:
            try:
                lang_data = requests.get(lang_url, headers=headers).json()
                for lang, bytes_count in lang_data.items():
                    languages[lang] += bytes_count
                    total_bytes += bytes_count
            except:
                pass

    # Calculate language percentages
    lang_percentages = []
    if total_bytes > 0:
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        for lang, bytes_count in sorted_langs[:5]:
            percentage = (bytes_count / total_bytes) * 100
            lang_percentages.append({"name": lang, "percentage": round(percentage, 1)})

    most_used_lang = lang_percentages[0]["name"] if lang_percentages else "N/A"

    # Calculate account age
    if user_data.get("created_at"):
        created = datetime.fromisoformat(
            user_data.get("created_at").replace("Z", "+00:00")
        )
        account_age_days = (datetime.now(created.tzinfo) - created).days
        account_age_years = account_age_days // 365
        account_age_months = (account_age_days % 365) // 30
    else:
        account_age_years = 0
        account_age_months = 0

    return {
        "followers": user_data.get("followers", 0),
        "following": user_data.get("following", 0),
        "public_repos": user_data.get("public_repos", 0),
        "private_repos": private_repos,
        "total_repos": total_repos,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "current_streak": streaks["current"],
        "longest_streak": streaks["longest"],
        "most_used_lang": most_used_lang,
        "languages": lang_percentages,
        "account_age_years": account_age_years,
        "account_age_months": account_age_months,
        "created_at": user_data.get("created_at", ""),
    }


def generate_svg(stats):
    """Generate beautiful SVG with enhanced stats"""
    # Format account age
    if stats["account_age_years"] > 0:
        age_str = f"{stats['account_age_years']}y {stats['account_age_months']}m"
    else:
        age_str = f"{stats['account_age_months']}m"

    # Generate language bars
    lang_bars = ""
    y_offset = 0
    for lang in stats["languages"][:5]:
        lang_name = lang["name"]
        lang_percent = lang["percentage"]
        bar_width = (lang_percent / 100) * 240  # Max width 240px

        lang_bars += f"""
    <g transform="translate(0, {y_offset})">
      <text x="0" y="16" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="{THEME['text']}">{lang_name}</text>
      <text x="250" y="16" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="{THEME['text_secondary']}" text-anchor="end">{lang_percent}%</text>
      <rect x="0" y="22" width="240" height="10" fill="{THEME['bg_secondary']}" rx="5"/>
      <rect x="0" y="22" width="{bar_width * 1.2}" height="10" fill="{THEME['accent']}" rx="5"/>
    </g>"""
        y_offset += 35

    svg = f"""<svg width="700" height="450" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:{THEME['bg']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{THEME['bg_secondary']};stop-opacity:1" />
    </linearGradient>
    <linearGradient id="circleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{THEME['warning']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:#ffa500;stop-opacity:1" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="700" height="450" fill="url(#cardGrad)" rx="12"/>

  <!-- Border -->
  <rect x="1" y="1" width="698" height="448" fill="none" stroke="{THEME['border']}" stroke-width="2" rx="12"/>

  <!-- Top Row: Stats in Boxes -->
  <g transform="translate(30, 25)">
    <!-- Followers Box -->
    <g>
      <rect x="0" y="0" width="120" height="70" fill="{THEME['bg_secondary']}" rx="8" stroke="{THEME['border']}" stroke-width="1"/>
      <text x="60" y="20" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="{THEME['text_secondary']}" text-anchor="middle">Followers</text>
      <text x="60" y="48" font-family="Segoe UI, Arial, sans-serif" font-size="26" font-weight="bold" fill="{THEME['accent']}" text-anchor="middle">{stats['followers']}</text>
    </g>

    <!-- Following Box -->
    <g transform="translate(140, 0)">
      <rect x="0" y="0" width="120" height="70" fill="{THEME['bg_secondary']}" rx="8" stroke="{THEME['border']}" stroke-width="1"/>
      <text x="60" y="20" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="{THEME['text_secondary']}" text-anchor="middle">Following</text>
      <text x="60" y="48" font-family="Segoe UI, Arial, sans-serif" font-size="26" font-weight="bold" fill="{THEME['accent']}" text-anchor="middle">{stats['following']}</text>
    </g>

    <!-- Public Repos Box -->
    <g transform="translate(280, 0)">
      <rect x="0" y="0" width="120" height="70" fill="{THEME['bg_secondary']}" rx="8" stroke="{THEME['border']}" stroke-width="1"/>
      <text x="60" y="20" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="{THEME['text_secondary']}" text-anchor="middle">Repos</text>
      <text x="60" y="48" font-family="Segoe UI, Arial, sans-serif" font-size="26" font-weight="bold" fill="{THEME['accent']}" text-anchor="middle">{stats['public_repos']}</text>
    </g>

    <!-- Total Stars Box -->
    <g transform="translate(420, 0)">
      <rect x="0" y="0" width="120" height="70" fill="{THEME['bg_secondary']}" rx="8" stroke="{THEME['border']}" stroke-width="1"/>
      <text x="60" y="20" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="{THEME['text_secondary']}" text-anchor="middle">Stars</text>
      <text x="60" y="48" font-family="Segoe UI, Arial, sans-serif" font-size="26" font-weight="bold" fill="{THEME['success']}" text-anchor="middle">{stats['total_stars']}</text>
    </g>

    <!-- Total Forks Box -->
    <g transform="translate(560, 0)">
      <rect x="0" y="0" width="120" height="70" fill="{THEME['bg_secondary']}" rx="8" stroke="{THEME['border']}" stroke-width="1"/>
      <text x="60" y="20" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="{THEME['text_secondary']}" text-anchor="middle">Forks</text>
      <text x="60" y="48" font-family="Segoe UI, Arial, sans-serif" font-size="26" font-weight="bold" fill="{THEME['accent_secondary']}" text-anchor="middle">{stats['total_forks']}</text>
    </g>
  </g>

  <!-- Middle Section: Current Streak Circle (Center) and Longest Streak (Right) -->
  <g transform="translate(0, 120)">
    <!-- Current Streak Circle in Middle -->
    <g transform="translate(350, 0)">
      <circle cx="0" cy="70" r="65" fill="url(#circleGrad)" filter="url(#glow)"/>
      <circle cx="0" cy="70" r="65" fill="none" stroke="{THEME['border']}" stroke-width="2"/>
      <text x="0" y="60" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="white" text-anchor="middle">Current</text>
      <text x="0" y="78" font-family="Segoe UI, Arial, sans-serif" font-size="32" font-weight="bold" fill="white" text-anchor="middle">{stats['current_streak']}</text>
      <text x="0" y="95" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="white" text-anchor="middle">days</text>
    </g>

    <!-- Longest Streak on Right -->
    <g transform="translate(520, 25)">
      <rect x="0" y="0" width="150" height="90" fill="{THEME['bg_secondary']}" rx="8" stroke="{THEME['border']}" stroke-width="1"/>
      <text x="75" y="22" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="{THEME['text_secondary']}" text-anchor="middle">Longest Streak</text>
      <text x="75" y="58" font-family="Segoe UI, Arial, sans-serif" font-size="36" font-weight="bold" fill="{THEME['success']}" text-anchor="middle" filter="url(#glow)">{stats['longest_streak']}</text>
      <text x="75" y="80" font-family="Segoe UI, Arial, sans-serif" font-size="11" fill="{THEME['text_secondary']}" text-anchor="middle">days</text>
    </g>
  </g>

  <!-- Bottom Section: Top Languages with Progress Bars -->
  <g transform="translate(30, 250)">
    <text x="0" y="0" font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="bold" fill="{THEME['text']}">Top Languages</text>
    {lang_bars}
  </g>

  <!-- Footer -->
  <g transform="translate(30, 420)">
    <text x="0" y="0" font-family="Segoe UI, Arial, sans-serif" font-size="10" fill="{THEME['text_secondary']}">
      Generated on {datetime.now().strftime("%B %d, %Y")} • @{USERNAME}
    </text>
    <circle cx="640" cy="5" r="3" fill="{THEME['success']}">
      <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
    </circle>
  </g>
</svg>"""

    return svg


def main():
    print("🚀 Fetching GitHub stats...")
    try:
        stats = get_github_stats()

        print("🎨 Generating beautiful SVG...")
        svg_content = generate_svg(stats)

        # Write to file
        output_path = "stats.svg"
        with open(output_path, "w") as f:
            f.write(svg_content)

        print(f"✅ Stats generated successfully! Saved to {output_path}")
        print(f"\n📊 Stats Summary:")
        print(f"  👥 Followers: {stats['followers']}")
        print(f"  ➕ Following: {stats['following']}")
        print(f"  📦 Public Repos: {stats['public_repos']}")
        print(f"  ⭐ Total Stars: {stats['total_stars']}")
        print(f"  🍴 Total Forks: {stats['total_forks']}")
        print(f"  🔥 Current Streak: {stats['current_streak']} days")
        print(f"  🏆 Longest Streak: {stats['longest_streak']} days")
        print(f"  💻 Most Used Language: {stats['most_used_lang']}")
        top_langs_str = ", ".join(
            [
                f"{lang['name']} ({lang['percentage']}%)"
                for lang in stats["languages"][:3]
            ]
        )
        print(f"  📚 Top Languages: {top_langs_str}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
