import feedparser

# Configurações do feed RSS e Bluesky
feed_url = 'http://www.hltv.org/news.rss.php'

feed = feedparser.parse(feed_url)

for entry in feed.entries:
    title = entry.title
    link = entry.link
    print(f'{title} - {link}')