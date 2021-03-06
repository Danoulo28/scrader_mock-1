import os
import pandas as pd
import Stemmer
from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics import f1_score
from sklearn.svm import SVC
from time import time
from pymongo import MongoClient
import logging
import requests
import string


logger = logging.getLogger('newapp')
hdlr = logging.FileHandler('algorithm.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

english_stemmer = Stemmer.Stemmer('en')


class StemmedTfidfVectorizer(TfidfVectorizer):

    def build_analyzer(self):
        analyzer = super(TfidfVectorizer, self).build_analyzer()
        return lambda doc: english_stemmer.stemWords(analyzer(doc))


def send_users_notification(database, company_name, article_id):
    users_collection = database['users']
    query = {'notification_type': 'Companies'}
    users = users_collection.find(query)
    logger.info('Checking if user follows {}'.format(company_name))
    for user in users:
        if company_name in user.get('companies'):
            url = 'https://api.chatfuel.com/bots/591189a0e4b0772d3373542b/' \
                  'users/{}/' \
                  'send?chatfuel_token=vnbqX6cpvXUXFcOKr5RHJ7psSpHDRzO1hXBY8dkvn50ZkZyWML3YdtoCnKH7FSjC' \
                  '&chatfuel_block_id=5ae5a2d9e4b0f617d6a06eee&last%20name={}&article={}'.\
                  format(user.get('user_id'), user.get('name'), article_id)
            logger.info(user.get('name'))
            try:
                requests.post(url)
            except requests.exceptions.RequestException:
                pass


def store_to_database(data, coll):
    dbcli = MongoClient('127.0.0.1', 8080)
    scrader_db = dbcli['scrader']
    scrader_db.authenticate('scrader', 'scr@d3r')
    existing_articles = scrader_db[coll]
    all_articles = data.to_dict('records')
    logger.info('checking to store {} artciles to database'.format(len(all_articles)))
    articles_stored = 0
    for article in all_articles:
        new_article = {}
        new_article['title'] = article.get('Title')
        new_article['image_url'] = article.get('Image')
        new_article['subtitle'] = article.get('Date')
        new_article['item_url'] = article.get('Article')
        new_article['direction'] = article.get('Sentiment')
        new_article['company'] = article.get('Company')
        new_article['website'] = article.get('Website')
        new_article['website_url'] = article.get('Website url')
        new_article['checked'] = False
        new_article['appended'] = False
        exists = existing_articles.find_one(
            {"title": article.get('Title')})
        if exists is None:
            articles_stored += 1
            art_id = existing_articles.insert_one(new_article).inserted_id

            # if coll == 'articles':
            #     send_users_notification(
            #         scrader_db,
            #         article.get('Company'),
            #         art_id
            #     )
    logger.info('storing {} to database'.format(articles_stored))


def train_classifier(clf, X_train, y_train):
    """ Fits a classifier to the training data. """
    # Start the clock, train the classifier, then stop the clock
    start = time()
    clf.fit(X_train, y_train)
    end = time()
    logger.info("Trained model in {:.4f} seconds".format(end - start))
    return clf


def predict_labels(clf, features):
    # Start the clock, make predictions, then stop the clock
    start = time()
    y_pred = clf.predict(features)
    end = time()
    logger.info("Made predictions in {:.4f} seconds.".format(end - start))
    return y_pred


def run_algorithm(filename):
    dbcli = MongoClient('127.0.0.1', 8080)
    db = dbcli['scrader']
    db.authenticate('scrader', 'scr@d3r')
    collection = db['scraper_companies']
    scraper_companies = list(collection.find({}, {'_id': False}))
    stop_words_list = []
    for comp in scraper_companies:
        stop_words_list.extend(comp.get('synonims'))

    data = pd.read_csv('./scraderdata.csv', sep=',', encoding='utf-8')

    for k in range(len(data)):
        data["title"][k] = data["title"][k].lower()
    for i in range(len(data)):
        data["title"][i] = data["title"][i].encode('utf-8').translate(None, string.punctuation)
    for j in range(len(data)):
        data["title"][j] = ''.join([i for i in data["title"][j] if not i.isdigit()])

    data1 = data['title']
    data2 = data['direction']

    data = pd.concat([data1.reset_index(drop=True), data2], axis=1)
    data.columns = ['title', 'direction']
    data.groupby(['direction']).count().reset_index()
    train_set = data
    train_set.groupby(['direction']).count().reset_index()
    data = data.sample(frac=1)

    # g = TfidfVectorizer(encoding='utf-8', min_df=3, max_df=10000,
    #                     ngram_range=(1, 2000), analyzer=u'char',
    #                     max_features=20000)
    # g = StemmedTfidfVectorizer(min_df=5, max_df=1000, ngram_range=(1, 6), stop_words=[
    #      "Amazon", "Uber", "Netflix", "Google", "Boeing", "IBM", "Aig", "Apple", "Ryanair", "Motorolla",
    #      "Equifax", "Microsoft", "Spotify", "Exxon", "Wells Fargo", "Toyota", "HSBC", "BP",
    #      "Volkswagen", "BnP Paribas", "Daimler", "Samsung", "AXA", "Vodafone", "Nestle", "Ford", "Metlife",
    #      "General Motors", "Intel", "Oracle", "Unilever", "Morgan Stanley", "Barclays", "Christian Dior", "3M",
    #      "Target", "Nintendo", "Tesla", "Panasonic", "ebay", "Kia", "Renault", "Apache", "Philips", "Monsanto",
    #      "Accenture", "Toshiba", "Baidu", "SKY", "JPMorgan", "JP-Morgan", "P&G", "VW", "BMW", "Benz", "Mercedes",
    #      "AT&T","Renault","Alibaba",  "Citi","Chevron","Wal-mart","Gazprom","Verizon", "Santander","Siemens","Novartis",
    #      "Goldman","Metlife","Hyundai", "Disney","Prudencial","Qualcomm","Honeywell","ABB","Astrazeneca","Carrefour","Canon",
    #      "Canon","Aetna"], analyzer=u'word', max_features=5000)
    g = StemmedTfidfVectorizer(min_df=5, max_df=1000, ngram_range=(1, 6), stop_words=stop_words_list,
                               analyzer=u'word', max_features=5000)
    X_train = g.fit_transform(data['title']).toarray()
    y_train = data['direction']

    clf = SVC(kernel='linear', probability=True)
    clf = train_classifier(clf, X_train, y_train)
    real_data = pd.read_csv(filename, sep=',',
                            encoding='utf-8')
    titles = g.transform(real_data['Title']).toarray()
    results = predict_labels(clf, titles)
    probabilities = clf.predict_proba(titles)
    list_probabilities = probabilities.tolist()
    best_probs = []
    for prob_combo in list_probabilities:
        best_probs.append(max(prob_combo))

    real_data['Sentiment'] = results
    real_data['Probability'] = best_probs
    live_data = real_data[real_data.Probability >= 0.7]

    store_to_database(real_data, 'dev_articles')
    store_to_database(live_data, 'articles')

    try:
        os.remove("./ScraderwithSentiment.csv")
    except OSError:
        pass
    real_data.to_csv("./ScraderwithSentiment.csv", encoding='utf-8')


if __name__ == '__main__':
    # run as script
    _file = "./Scraderlatestnews.csv"
    run_algorithm(_file)
