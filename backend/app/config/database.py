from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

load_dotenv()

mongo = PyMongo()

def init_db(app):
    app.config["MONGO_URI"] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/finplanner')
    mongo.init_app(app)
    return mongo