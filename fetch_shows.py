import re
import os
import datetime
from playwright.sync_api import sync_playwright

current_year = datetime.datetime.utcnow().year

url = (
    f"https://bingebase.com/tv"
    f"?sort=recent&year_from={current_year}&year_to="
    f"&seasons=1&country%5B%5D=US&country%5B%5D=GB&language%5B%5D=en"
)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(user_agent="Mozilla/5.0 (compatible; RSSFeedBot/1.0)")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_selector('img[alt*="poster"]', timeout=30000)
    except Exception as e:
        print(f"Warning: poster selector never appeared - {e}")
    page.wait_for_timeout(2000)
    html = page.content()
    browser.close()

pattern = re.compile(
    r'data-media-card-rating-value="([\d.]*)"'
    r'(?:(?!data-media-card-rating-value=").)*?'
    r'data-media-card-target="posterLink"[^>]+href="(/tv/[^"]+)"[^>]*>\s*'
    r'<img[^>]+alt="([^"]+?) poster"[^>]+src="(https://cdn\.bingebase\.com/[^"]+)"',
    re.DOTALL
)

all_matches = pattern.findall(html)

# only keep shows rated 1.0 or above (0.0/blank usually means "not yet rated")
matches = [m for m in all_matches if m[0] and float(m[0]) >= 1.0][:5]

print(f"Total cards found: {len(all_matches)}")
print(f"Found {len(matches)} shows")

q = chr(34)
items_xml = ""

for rating, href, title, poster in matches:
    title_clean = title.replace("&", "&amp;")
    link = f"https://bingebase.com{href}"
    items_xml += "<item>"
    items_xml += f"<title>{title_clean}</title>"
    items_xml += "<description>" + chr(60) + "![CDATA[" + \
        f'<img src=' + q + poster + q + '>' + \
        "]]" + chr(62) + "</description>"
    items_xml += f"<link>{link}</link>"
    items_xml += "</item>"

rss = '<?xml version=' + q + '1.0' + q + ' encoding=' + q + 'UTF-8' + q + '?>'
rss += "<rss version=" + q + "2.0" + q + ">"
rss += "<channel>"
rss += "<title>New TV Shows</title>"
rss += "<link>https://foxyoo5.github.io/BingeBase-New-TV-Shows/new-tv-shows.xml</link>"
rss += "<description>Latest TV shows from BingeBase</description>"
rss += items_xml
rss += "</channel></rss>"

os.makedirs("docs", exist_ok=True)
with open("docs/new-tv-shows.xml", "w", encoding="utf-8") as f:
    f.write(rss)
