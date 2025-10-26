from datetime import datetime
from app.config.database import mongo

class Budget:
    collection = mongo.db.budgets
    
    @staticmethod
    def create(user_id, data):
        budget = {
            'user_id': user_id,
            'category': data['category'],
            'amount': float(data['amount']),
            'period': data.get('period', 'monthly'),
            'created_at': datetime.utcnow()
        }
        result = Budget.collection.insert_one(budget)
        budget['_id'] = str(result.inserted_id)
        return budget
    
    @staticmethod
    def find_by_user(user_id):
        budgets = list(Budget.collection.find({'user_id': user_id}))
        for b in budgets:
            b['_id'] = str(b['_id'])
        return budgets