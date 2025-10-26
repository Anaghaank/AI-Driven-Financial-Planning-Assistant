from datetime import datetime
from app.config.database import mongo
from bson import ObjectId

class Transaction:
    collection = mongo.db.transactions
    
    @staticmethod
    def create(user_id, data):
        transaction = {
            'user_id': user_id,
            'amount': float(data['amount']),
            'category': data['category'],
            'description': data.get('description', ''),
            'date': data.get('date', datetime.utcnow()),
            'type': data['type'],
            'created_at': datetime.utcnow()
        }
        result = Transaction.collection.insert_one(transaction)
        transaction['_id'] = str(result.inserted_id)
        return transaction
    
    @staticmethod
    def find_by_user(user_id, limit=100):
        transactions = list(Transaction.collection.find({'user_id': user_id}).sort('date', -1).limit(limit))
        for t in transactions:
            t['_id'] = str(t['_id'])
            # Convert datetime to ISO string for JSON serialization
            if isinstance(t.get('date'), datetime):
                t['date'] = t['date'].isoformat()
            if isinstance(t.get('created_at'), datetime):
                t['created_at'] = t['created_at'].isoformat()
        return transactions
    
    @staticmethod
    def get_analytics(user_id):
        pipeline = [
            {'$match': {'user_id': user_id}},
            {'$group': {
                '_id': '$category',
                'total': {'$sum': '$amount'},
                'count': {'$sum': 1}
            }}
        ]
        return list(Transaction.collection.aggregate(pipeline))
    
    @staticmethod
    def delete(transaction_id, user_id):
        result = Transaction.collection.delete_one({'_id': ObjectId(transaction_id), 'user_id': user_id})
        return result.deleted_count > 0