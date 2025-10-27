from datetime import datetime
from app.config.database import mongo
from bson import ObjectId

class Bank:
    collection = mongo.db.banks
    
    @staticmethod
    def create(user_id, data):
        bank = {
            'user_id': user_id,
            'bank_name': data['bank_name'],
            'account_number': data['account_number'],
            'account_type': data.get('account_type', 'Checking'),
            'balance': float(data.get('balance', 0)),
            'last_statement_date': data.get('last_statement_date'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = Bank.collection.insert_one(bank)
        bank['_id'] = str(result.inserted_id)
        return bank
    
    @staticmethod
    def find_by_user(user_id):
        banks = list(Bank.collection.find({'user_id': user_id}))
        for b in banks:
            b['_id'] = str(b['_id'])
        return banks
    
    @staticmethod
    def find_by_account(user_id, account_number):
        return Bank.collection.find_one({'user_id': user_id, 'account_number': account_number})
    
    @staticmethod
    def update(bank_id, user_id, data):
        data['updated_at'] = datetime.utcnow()
        Bank.collection.update_one(
            {'_id': ObjectId(bank_id), 'user_id': user_id},
            {'$set': data}
        )
        return Bank.collection.find_one({'_id': ObjectId(bank_id)})