from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import logging

def get_db_connection():
    client = MongoClient(os.getenv('MONGO_URI'), server_api=ServerApi('1'))
    try:
        client.admin.command('ping')
        quire_db = client.get_database('glovera_db')
        print("connected to db!")
        logging.info("Successfully connected to MongoDB!")
        return quire_db
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        raise

def get_conversations_collection():
    db = get_db_connection()
    return db.get_collection('Conversation') 


def get_programs_collection():
    db = get_db_connection()
    return db.get_collection('ProgramsGloveraFinal')

def get_collection_by_name(db, collection_name):
    return db.get_collection(collection_name)