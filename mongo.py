from pymongo import MongoClient
import companies


def init_database():

    global client
    client = MongoClient()
    global db
    db = client['scrader']
    companies_stored = db['companies']
    if companies_stored.count() == 0:
        insert_many('companies', companies.all_companies)

    return db


def insert_one(collection_name, document):
    collection = db[collection_name]
    return collection.insert_one(document)


def delete_many(collection_name):
    collection = db[collection_name]
    return collection.delete_many({})


def count(collection_name):
    return db[collection_name].count()


def fetch_collection(collection_name):
    collection = db[collection_name]
    return collection.find({}, {'_id': False})


def find_matches(collection_name, to_match):
    collection = db[collection_name]
    return collection.find(to_match)


def find_matches_not_containing(collection_name, key, value):
    collection = db[collection_name]
    return collection.find({key: {'$nin': value}})


def find_one_match(collection_name, to_match):
    collection = db[collection_name]
    return collection.find_one(to_match)


def insert_one_in(collection_name, to_match, new_data):
    collection = db[collection_name]
    return collection.update(to_match, {'$set': new_data})


def remove_one_from(collection_name, to_match, data_to_remove):
    collection = db[collection_name]
    return collection.update(to_match, {'$unset': data_to_remove})

def insert_many(collection_name, to_add):
    collection = db[collection_name]
    return collection.insert_many(to_add)



