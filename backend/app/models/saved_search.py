from datetime import datetime
from app.config.database import mongo
from bson import ObjectId

class SavedSearch:
    collection = mongo.db.saved_searches
    
    @staticmethod
    def create(user_id, data):
        """Create a new saved search"""
        saved_search = {
            'user_id': user_id,
            'name': data['name'],
            'filters': data.get('filters', {}),
            'created_at': datetime.utcnow(),
            'last_used': None,
            'use_count': 0
        }
        
        result = SavedSearch.collection.insert_one(saved_search)
        saved_search['_id'] = str(result.inserted_id)
        return saved_search
    
    @staticmethod
    def find_by_user(user_id):
        """Get all saved searches for a user"""
        searches = list(SavedSearch.collection.find({'user_id': user_id}).sort('created_at', -1))
        
        for search in searches:
            search['_id'] = str(search['_id'])
            if isinstance(search.get('created_at'), datetime):
                search['created_at'] = search['created_at'].isoformat()
            if isinstance(search.get('last_used'), datetime):
                search['last_used'] = search['last_used'].isoformat()
        
        return searches
    
    @staticmethod
    def get_by_id(search_id, user_id):
        """Get a saved search by ID"""
        search = SavedSearch.collection.find_one({
            '_id': ObjectId(search_id),
            'user_id': user_id
        })
        
        if search:
            search['_id'] = str(search['_id'])
            if isinstance(search.get('created_at'), datetime):
                search['created_at'] = search['created_at'].isoformat()
            if isinstance(search.get('last_used'), datetime):
                search['last_used'] = search['last_used'].isoformat()
        
        return search
    
    @staticmethod
    def update_usage(search_id, user_id):
        """Update last used timestamp and increment use count"""
        SavedSearch.collection.update_one(
            {'_id': ObjectId(search_id), 'user_id': user_id},
            {
                '$set': {'last_used': datetime.utcnow()},
                '$inc': {'use_count': 1}
            }
        )
    
    @staticmethod
    def update(search_id, user_id, data):
        """Update a saved search"""
        update_data = {}
        
        if 'name' in data:
            update_data['name'] = data['name']
        if 'filters' in data:
            update_data['filters'] = data['filters']
        
        update_data['updated_at'] = datetime.utcnow()
        
        result = SavedSearch.collection.update_one(
            {'_id': ObjectId(search_id), 'user_id': user_id},
            {'$set': update_data}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def delete(search_id, user_id):
        """Delete a saved search"""
        result = SavedSearch.collection.delete_one({
            '_id': ObjectId(search_id),
            'user_id': user_id
        })
        return result.deleted_count > 0