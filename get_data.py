import get_news
import get_scholar
import mongo_utils
import datetime
import logging
import logging.config
from logsetup import LOGGING_CONFIG


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
logger.info('Started get_data.py!')


def create_job_query(q, search_engines):
    collection = mongo_utils.connect_to_database(collection_name=mongo_utils.QUERIES_COLLECTION)
    query = {
        'q': q,
        'created_at': datetime.datetime.utcnow(),
        'search_engines': search_engines
    }
    mongo_utils.post_query(collection, query)


def retrieve_data(q, search_engines):
    collection = mongo_utils.connect_to_database(collection_name=mongo_utils.QUERIES_COLLECTION)
    logging.info("Starting search for query='{}' and search engines={}".format(q, search_engines))
    delete_dangling_jobs()

    if 'news' in search_engines:
        get_news.get_news(q)
    if 'scholar' in search_engines:
        get_scholar.get_scholar(q)

    query = {
        'q': q,
        'search_engines': search_engines,
        'updated_at': datetime.datetime.utcnow()
    }
    mongo_utils.post_query(collection, query, upsert=False)


def delete_dangling_jobs():
    df = mongo_utils.read_mongo_news_collection(collection_name=mongo_utils.QUERIES_COLLECTION,
                                                query={})

    collection = mongo_utils.connect_to_database(collection_name=mongo_utils.QUERIES_COLLECTION)
    for index, row in df.iterrows():
        try:
            if "created_at" in row and "updated_at" not in row:
                now = datetime.datetime.utcnow()
                if now - row["created_at"] > datetime.timedelta(hours=6):
                    mongo_utils.delete(collection, row['query'])
        except:
            logging.exception("Failed detecting dangling record for row='{}'".format(row))


def check_last_query(q, search_engines):
    df = mongo_utils.read_mongo_news_collection(collection_name=mongo_utils.QUERIES_COLLECTION,
                                                query={'q': q.lower(), 'search_engines': search_engines})
    if not df.empty:
        created_at = df.iloc[0]['created_at']
        now = datetime.datetime.utcnow()
        if (now - created_at > datetime.timedelta(days=7)):
            return True
        else:
            logging.info("Skipping search, since we already have a recent data for this query")
    else:
        return True


if __name__ == '__main__':
    # collection = mongo_utils.connect_to_database(collection_name=mongo_utils.QUERIES_COLLECTION)
    # q = "ambient computing1"
    # query = {
    #     'q': q,
    #     'updated_at': datetime.datetime.utcnow(),
    #     'search_engines': ['news', 'scholar']
    # }
    # mongo_utils.post_query(collection, query)

    query_string = 'Post yellow fever vaccine encephalitis'
    search_engines = ['scholar']
    logging.info("checking last query")
    if check_last_query(query_string, search_engines):
        logging.info("retreiveing data")
        retrieve_data(query_string, search_engines)
