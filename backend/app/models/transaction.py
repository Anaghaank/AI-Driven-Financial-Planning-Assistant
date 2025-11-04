from datetime import datetime
from app.config.database import mongo
from bson import ObjectId
import re

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
    def find_duplicate(user_id, date, amount, description_prefix):
        """Check if similar transaction already exists to prevent duplicates"""
        try:
            # Convert date string to datetime if needed
            if isinstance(date, str):
                from dateutil import parser as date_parser
                date = date_parser.parse(date)
            
            # Check for exact match first
            exact_match = Transaction.collection.find_one({
                'user_id': user_id,
                'date': date,
                'amount': float(amount)
            })
            
            if exact_match:
                return exact_match
            
            # If no exact match, check for similar description on same date
            similar = Transaction.collection.find_one({
                'user_id': user_id,
                'date': date,
                'amount': float(amount),
                'description': {'$regex': f'^{re.escape(description_prefix[:30])}', '$options': 'i'}
            })
            
            return similar
            
        except Exception as e:
            print(f"Error checking duplicate: {e}")
            return None
    
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
    def get_by_date_range(user_id, start_date, end_date):
        """Get transactions within a date range"""
        transactions = list(Transaction.collection.find({
            'user_id': user_id,
            'date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }).sort('date', -1))
        
        for t in transactions:
            t['_id'] = str(t['_id'])
            if isinstance(t.get('date'), datetime):
                t['date'] = t['date'].isoformat()
            if isinstance(t.get('created_at'), datetime):
                t['created_at'] = t['created_at'].isoformat()
        
        return transactions
    
    @staticmethod
    def get_category_breakdown(user_id, transaction_type=None):
        """Get spending/income breakdown by category"""
        match_query = {'user_id': user_id}
        if transaction_type:
            match_query['type'] = transaction_type
        
        pipeline = [
            {'$match': match_query},
            {'$group': {
                '_id': '$category',
                'total': {'$sum': '$amount'},
                'count': {'$sum': 1},
                'avg': {'$avg': '$amount'}
            }},
            {'$sort': {'total': -1}}
        ]
        
        results = list(Transaction.collection.aggregate(pipeline))
        
        # Format results
        for result in results:
            result['category'] = result.pop('_id')
        
        return results
    
    @staticmethod
    def delete(transaction_id, user_id):
        result = Transaction.collection.delete_one({'_id': ObjectId(transaction_id), 'user_id': user_id})
        return result.deleted_count > 0
    
    @staticmethod
    def update(transaction_id, user_id, data):
        """Update a transaction"""
        update_data = {}
        
        if 'amount' in data:
            update_data['amount'] = float(data['amount'])
        if 'category' in data:
            update_data['category'] = data['category']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'date' in data:
            update_data['date'] = data['date']
        if 'type' in data:
            update_data['type'] = data['type']
        
        update_data['updated_at'] = datetime.utcnow()
        
        result = Transaction.collection.update_one(
            {'_id': ObjectId(transaction_id), 'user_id': user_id},
            {'$set': update_data}
        )
        
        return result.modified_count > 0