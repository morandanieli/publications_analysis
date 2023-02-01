import random
import redis
from rq import Queue

import get_data
import mongo_utils
from flask import Flask, render_template, request, jsonify, redirect
from get_data import check_last_query, retrieve_data
import logging.config
from logsetup import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
logger.warning('Started app.py!')


app = Flask(__name__)
r = redis.Redis()
que = Queue(connection=r, default_timeout=10*60*60)

POSSIBLE_TOPICS = [
    'Iran Nuclear Deal',
    'Abraham Accords',
    'Russia Ukraine war',
    'Quiet Quitting',
    'The Great Resignation',
    'Passive Income',
    'Economics of Sea Transport and International Trade',
    'Urban agriculture',
    'Cultivated meat'
]


def make_clickable(url, name):
    return '<a href="{}" rel="noopener noreferrer" target="_blank">{}</a>'.format(url,name)


def make_clickable_same_page(url, name):
    return '<a href="{}" rel="noopener noreferrer">{}</a>'.format(url,name)

base_html = """
<!doctype html>
<html><head>
<meta http-equiv="Content-type" content="text/html; charset=utf-8">
<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.2/jquery.min.js"></script>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.16/css/jquery.dataTables.css">
<script type="text/javascript" src="https://cdn.datatables.net/1.10.16/js/jquery.dataTables.js"></script>
</head><body>%s<script type="text/javascript">$(document).ready(function(){$('table').DataTable({
    "pageLength": 10,
    order: [[0, 'desc']]
});});</script>
</body></html>
"""


def get_df_as_html(df, columns=None, highlight_scores=False):
    df_as_html = df.to_html(
        columns=columns,
        index=False, escape=False, classes='table table-striped table-hover',
        justify='left')

    if highlight_scores:
        scores = list(df.Score.value_counts().index)
        for score in scores:
            if score > 0:
                df_as_html = df_as_html.replace("""<tr>
      <td>{}</td>""".format(score), '<tr style = "background-color: #4fff14;"><td>{}</td>'.format(score))

    return base_html % df_as_html


@app.route("/refresh_news")
def refresh_news():
    args = request.args
    query_string = args['q']

    df = mongo_utils.read_mongo_news_collection(query={'query_string': query_string.lower()})
    if df.empty:
        return jsonify({"news": "Processing data..."})

    df['publisher_name'] = df['publisher'].apply(lambda x: x['title'])
    df['link'] = df.apply(lambda x: make_clickable(x['url'], x['publisher_name'] if x['publisher_name'] != 'NA' else x['url'][:50] + "..."), axis=1)
    df['Analytics'] = df['url'].apply(lambda x: make_clickable('/analyze_doc?url={}'.format(x), 'Analyze'))
    cols = {
        'sub_count': 'Score',
        'article_title': 'Article',
        'link': 'Link',
        'sub_toks': 'Tags',
        'origin': 'Origin',
        'description': 'Description',
        'published_year': 'Published Year'
    }
    df.rename(cols, inplace=True, axis=1)
    cols = ['Score', 'Article', 'Tags', 'Description', 'Published Year', 'Link', 'Origin', 'Analytics']
    return jsonify({"news": get_df_as_html(df, cols, highlight_scores=True)})


@app.route("/refresh_jobs")
def refresh_jobs():
    df = mongo_utils.read_mongo_news_collection(collection_name=mongo_utils.QUERIES_COLLECTION,
                                                query={})
    if df.empty:
        return jsonify({"jobs": "There are no jobs"})
    df['Query'] = df['q'].apply(lambda x: make_clickable_same_page('/search?q={}'.format(x), x))
    df['Search Engines'] = df['search_engines']
    if 'updated_at' not in df:
        df['updated_at'] = "-"
    cols = {
        'created_at': 'Start Time',
        'updated_at': 'End Time'
    }
    df.rename(cols, inplace=True, axis=1)
    return jsonify({"jobs": get_df_as_html(df, columns=['Start Time', 'End Time', 'Query', 'Search Engines'])})


@app.route("/search")
def search():
    args = request.args
    query_string = args['q']

    if not query_string:
        query_string = random.choice(POSSIBLE_TOPICS)

    search_engines = []
    if 'news' in args:
        search_engines.append('news')
    if 'scholar' in args:
        search_engines.append('scholar')

    if query_string and check_last_query(query_string, search_engines):
        logging.info("Creating job query")
        get_data.create_job_query(query_string, search_engines)
        logging.info("Push to queue")
        job = que.enqueue(retrieve_data, query_string, search_engines)
        print(job)
        # TODO stop refresh data when job is done

    return render_template('search.html', query_string=query_string)


@app.route("/jobs")
def jobs():
    return render_template('jobs.html')


@app.route("/")
def index():
    placeholder = random.choice(POSSIBLE_TOPICS)
    return render_template('index.html', placeholder=placeholder)


@app.route("/analyze_doc")
def analyze_doc():
    #TODO
    args = request.args
    url = args['url']
    data = mongo_utils.get_by_id(url)
    return render_template('doc_analyzer.html', doc=data['article_text'],
                           title=data['article_title'])


if __name__ == '__main__':
    app.run(debug=True, port=5001)