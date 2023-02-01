import logging
import re

import doc_analyzer
from GNews.gnews import gnews
import mongo_utils


IGNORE_TITLES = ['Subscribe to read', 'Register to read']


def get_news(query_string, language='en', search_region='US', search_period='1w', limit=100):
    collection = mongo_utils.connect_to_database()
    queries = query_string.lower().split()
    googlenews = gnews.GNews(language=language, country=search_region,
                             period=search_period, max_results=limit)
                             #user_agent='Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)')
    results = googlenews.get_news(query_string)
    for res in results:
        url = res['url']
        try:
            article = googlenews.get_full_article(url)
            text = article.text
            title = article.title or res['title']

            res['article_text'] = text
            res['article_title'] = title
        except Exception:
            logging.warning("failed extracting article from url '{}'".format(url))
            continue

        if title in IGNORE_TITLES:
            logging.warning("skipping title '{}', since article is unreachable".format(title))
            continue

        res['query_string'] = query_string.lower()
        res['queries'] = queries
        res['origin'] = "news"

        res['published_year'] = re.findall("2\d{3}", res['published date'])[0]
        doc_analyzer.analyze_title(title, queries, res)
        mongo_utils.post_database(collection, res)


if __name__ == '__main__':
    lang = 'en'
    region = 'US'
    period = '1y'
    query = 'Abraham Accords'
    get_news(query, lang, region, period, limit=3)



