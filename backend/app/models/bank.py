from datetime import datetime
from app.config.database import mongo
from bson import ObjectId
import re

class Bank:
    collection = mongo.db.banks
    
    @staticmethod
    def create(user_id, data):
        bank = {
            'user_id': user_id,
            'bank_name': data['bank_name'],
            'account_number': data['account_number'],
            'account_type': data.get('account_type', 'Savings'),
            'balance': float(data.get('balance', 0)),
            'is_active': data.get('is_active', True),
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
            if isinstance(b.get('last_statement_date'), datetime):
                b['last_statement_date'] = b['last_statement_date'].isoformat()
            if isinstance(b.get('created_at'), datetime):
                b['created_at'] = b['created_at'].isoformat()
            if isinstance(b.get('updated_at'), datetime):
                b['updated_at'] = b['updated_at'].isoformat()
        return banks
    
    @staticmethod
    def find_by_account(user_id, account_number):
        """Find bank by account number (supports partial matching for masked numbers)"""
        # First try exact match
        bank = Bank.collection.find_one({'user_id': user_id, 'account_number': account_number})
        
        # If not found and account_number contains wildcards (****), try pattern matching
        if not bank and '****' in account_number:
            last_digits = account_number.replace('*', '')
            # Find account ending with these digits
            regex_pattern = f'.*{re.escape(last_digits)}$'
            bank = Bank.collection.find_one({
                'user_id': user_id,
                'account_number': {'$regex': regex_pattern}
            })
        
        if bank:
            bank['_id'] = str(bank['_id'])
        return bank
    
    @staticmethod
    def update(bank_id, user_id, data):
        data['updated_at'] = datetime.utcnow()
        Bank.collection.update_one(
            {'_id': ObjectId(bank_id), 'user_id': user_id},
            {'$set': data}
        )
        bank = Bank.collection.find_one({'_id': ObjectId(bank_id)})
        if bank:
            bank['_id'] = str(bank['_id'])
            if isinstance(bank.get('last_statement_date'), datetime):
                bank['last_statement_date'] = bank['last_statement_date'].isoformat()
            if isinstance(bank.get('created_at'), datetime):
                bank['created_at'] = bank['created_at'].isoformat()
            if isinstance(bank.get('updated_at'), datetime):
                bank['updated_at'] = bank['updated_at'].isoformat()
        return bank
    
    @staticmethod
    def update_balance(bank_id, new_balance):
        """Update bank balance"""
        Bank.collection.update_one(
            {'_id': ObjectId(bank_id)},
            {'$set': {
                'balance': float(new_balance),
                'updated_at': datetime.utcnow()
            }}
        )
        return True
    
    @staticmethod
    def get_total_balance(user_id):
        """Get total balance across all active banks"""
        banks = list(Bank.collection.find({
            'user_id': user_id,
            'is_active': {'$ne': False}  # Include banks without is_active field and those with is_active=True
        }))
        total = sum(b.get('balance', 0) for b in banks)
        return total
    
    @staticmethod
    def get_by_id(bank_id):
        """Get bank by ID"""
        bank = Bank.collection.find_one({'_id': ObjectId(bank_id)})
        if bank:
            bank['_id'] = str(bank['_id'])
            if isinstance(bank.get('last_statement_date'), datetime):
                bank['last_statement_date'] = bank['last_statement_date'].isoformat()
            if isinstance(bank.get('created_at'), datetime):
                bank['created_at'] = bank['created_at'].isoformat()
            if isinstance(bank.get('updated_at'), datetime):
                bank['updated_at'] = bank['updated_at'].isoformat()
        return bank
    
    @staticmethod
    def delete(bank_id, user_id):
        """Soft delete - mark as inactive"""
        result = Bank.collection.update_one(
            {'_id': ObjectId(bank_id), 'user_id': user_id},
            {'$set': {
                'is_active': False,
                'updated_at': datetime.utcnow()
            }}
        )
        return result.modified_count > 0
    
    @staticmethod
    def hard_delete(bank_id, user_id):
        """Permanently delete bank account"""
        result = Bank.collection.delete_one({
            '_id': ObjectId(bank_id),
            'user_id': user_id
        })
        return result.deleted_count > 0