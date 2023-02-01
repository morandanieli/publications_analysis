import pymongo
import logging
import pandas as pd

NEWS_DB_NAME = 'news'
NEWS_COLLECTION = 'news_analytics'
QUERIES_COLLECTION = 'queries'


def connect_to_database(host='localhost', port=27017, db_name=NEWS_DB_NAME, collection_name=NEWS_COLLECTION):
    try:
        cluster = pymongo.MongoClient(host, port)
        db = cluster[db_name]
        collection = db[collection_name]

        return collection

    except Exception as e:
        print("Connection Error.", e)


def post_database(collection, news):
    """post unique news articles to mongodb database"""
    doc = {
        "_id": news['url'],
        "description": news['description'],
        "published_year": news['published_year'],
        "url": news['url'],
        "publisher": news['publisher'],
        'num_citations': news['num_citations'] if 'num_citations' in news else None,
        # searched query
        'query_string': news['query_string'],
        'queries': news['queries'],

        # original article
        'article_text': news['article_text'],
        'article_title': news['article_title'],

        # analyzed data
        'sub_toks': news['sub_toks'],
        'sub_toks_l': news['sub_toks_l'],
        'sub_count': news['sub_count'],
        'remaining_sub_count': news['remaining_sub_count'],
        'weighted_sub_count': news['weighted_sub_count'],
        "origin": news['origin']
    }

    try:
        collection.update_one(doc, {'$set': doc}, upsert=True)
    except pymongo.errors.DuplicateKeyError:
        logging.error("Posting to database failed due to duplicate key.")


def post_query(collection, query, upsert=True):
    doc = {
        "_id": query['q'].lower(),
        "q": query['q'].lower(),
        'search_engines': query['search_engines']
    }
    if 'updated_at' in query:
        doc["updated_at"] = query['updated_at']
    else:
        doc["created_at"] = query['created_at']

    try:
        collection.update_one(doc, {'$set': doc}, upsert=upsert)
    except pymongo.errors.DuplicateKeyError:
        logging.error("Posting to database failed due to duplicate key.")


def delete(collection, query):
    collection.delete_one({"_id": query})


def read_mongo_news_collection(query={}, no_id=True, db_name=NEWS_DB_NAME, collection_name=NEWS_COLLECTION):
    """ Read from Mongo and Store into DataFrame """
    # Connect to MongoDB
    collection = connect_to_database(db_name=db_name, collection_name=collection_name)
    # Make a query to the specific DB and Collection
    cursor = collection.find(query)
    # Expand the cursor and construct the DataFrame
    df = pd.DataFrame(list(cursor))

    # Delete the _id
    if no_id and '_id' in df:
        del df['_id']

    return df


def get_by_id(id):
    collection = connect_to_database()
    return collection.find_one({'url': id})