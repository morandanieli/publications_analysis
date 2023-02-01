import time

import requests
from scholarly.scholarly import scholarly, ProxyGenerator
import mongo_utils
import logging
import doc_analyzer
from scihub.scihub.scihub import SciHub
from tika import parser
from tika import language as tlang

import logging.config
from logsetup import LOGGING_CONFIG


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
logger.info('Started get_scholar.py!')

sh = SciHub()
temp_file = '/tmp/paper.pdf'
SCRAPPER_API_KEY = '<<FILL HERE>>'


def get_scholar(query_string, language='en', search_region='US', limit=10000):
    collection = mongo_utils.connect_to_database()
    queries = query_string.lower().split()

    # use proxy
    logging.info("proxy setup start")
    pg = ProxyGenerator()
    pg.ScraperAPI(SCRAPPER_API_KEY)
    scholarly.use_proxy(pg, pg)
    logging.info("proxy setup done")

    # search
    logging.info("Searching publications")
    search_query = scholarly.search_pubs(query_string, language=language)
    logging.info("Done searching publications")
    counter = 0
    while counter < limit:
        try:
            logging.info("get next result from query")
            res = next(search_query)
            counter += 1
            if 'pub_url' not in res:
                logging.info("Pub url not found skipping res={}".format(res))
                continue
            res['url'] = res['pub_url']
            bib = res['bib']
            res['publisher'] = {}
            res['publisher']['title'] = bib['venue']
            res['description'] = bib['abstract']
            res['article_title'] = bib['title']

            try:
                l = tlang.from_buffer(res['article_title'])
                if l and l != language:
                    logging.info("Skipping article title '{}' since it's not in selected language '{}', current language='{}'".format(res['article_title'], language, l))
                    continue
            except Exception:
                logging.exception("Failed detecting language")

            res['published_year'] = bib['pub_year']
            try:
                logging.info("downloading url")
                if res['url'].endswith('.pdf'):
                    content = requests.get(res['url'])
                    with open(temp_file, 'wb') as f:
                        f.write(content.content)
                else:
                    sh.download(res['url'], path=temp_file)

                time.sleep(2)
                logging.info("parsing file")
                raw = parser.from_file(temp_file)
                # if 'Content-Language' in raw['metadata'] and raw['metadata']['Content-Language'] != language:
                #     logging.info(
                #         "Skipping article '{}' since it's not in selected language '{}'".format(res['article_title'],
                #                                                                                       language))
                #     continue
                res['article_text'] = raw['content']

            except Exception:
                res['article_text'] = None
                logging.exception("failed extracting article from url '{}'".format(res['url']))
                # continue

            res['query_string'] = query_string.lower()
            res['queries'] = queries
            res['origin'] = "research"

            logging.info("analyze title")
            doc_analyzer.analyze_title(res['article_title'], queries, res)
            if not res['sub_toks'] and res['description']:
                logging.info("analyze description")
                doc_analyzer.analyze_title(res['description'], queries, res)
            logging.info("post to db")
            mongo_utils.post_database(collection, res)
        except StopIteration:
            break

    logging.info("viewed {} results".format(counter-1))


if __name__ == '__main__':
    lang = 'en'
    region = 'US'
    period = '1y'
    query_string = 'Abraham Accords'
    get_scholar(query_string,language=lang, search_region=region, limit=2)
