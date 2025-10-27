from datetime import datetime
from app.config.database import mongo
from bson import ObjectId

class StatementUpload:
    collection = mongo.db.statement_uploads
    
    @staticmethod
    def create(user_id, data):
        statement = {
            'user_id': user_id,
            'bank_id': data.get('bank_id'),
            'filename': data['filename'],
            'file_hash': data['file_hash'],
            'statement_date': data.get('statement_date'),
            'transactions_count': data.get('transactions_count', 0),
            'status': 'processed',
            'uploaded_at': datetime.utcnow()
        }
        result = StatementUpload.collection.insert_one(statement)
        statement['_id'] = str(result.inserted_id)
        return statement
    
    @staticmethod
    def find_by_hash(user_id, file_hash):
        return StatementUpload.collection.find_one({'user_id': user_id, 'file_hash': file_hash})
    
    @staticmethod
    def find_by_user(user_id):
        statements = list(StatementUpload.collection.find({'user_id': user_id}).sort('uploaded_at', -1))
        for s in statements:
            s['_id'] = str(s['_id'])
        return statements