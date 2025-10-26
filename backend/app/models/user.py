from datetime import datetime
from app.config.database import mongo
import bcrypt

class User:
    collection = mongo.db.users
    
    @staticmethod
    def create(data):
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        user = {
            'email': data['email'],
            'name': data['name'],
            'password': hashed_password,
            'created_at': datetime.utcnow()
        }
        result = User.collection.insert_one(user)
        user['_id'] = str(result.inserted_id)
        return user
    
    @staticmethod
    def find_by_email(email):
        return User.collection.find_one({'email': email})
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)