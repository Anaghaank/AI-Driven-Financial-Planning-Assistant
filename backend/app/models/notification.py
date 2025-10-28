from datetime import datetime
from app.config.database import mongo

class Notification:
    collection = mongo.db.notifications
    
    @staticmethod
    def create(user_id, data):
        notification = {
            'user_id': user_id,
            'title': data['title'],
            'message': data['message'],
            'type': data.get('type', 'info'),  # info, warning, success, error
            'read': False,
            'created_at': datetime.utcnow()
        }
        result = Notification.collection.insert_one(notification)
        notification['_id'] = str(result.inserted_id)
        return notification
    
    @staticmethod
    def find_by_user(user_id, unread_only=False):
        query = {'user_id': user_id}
        if unread_only:
            query['read'] = False
        
        notifications = list(Notification.collection.find(query).sort('created_at', -1).limit(50))
        for n in notifications:
            n['_id'] = str(n['_id'])
        return notifications
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        from bson import ObjectId
        result = Notification.collection.update_one(
            {'_id': ObjectId(notification_id), 'user_id': user_id},
            {'$set': {'read': True}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def mark_all_as_read(user_id):
        result = Notification.collection.update_many(
            {'user_id': user_id, 'read': False},
            {'$set': {'read': True}}
        )
        return result.modified_count