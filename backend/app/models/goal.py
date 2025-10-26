from datetime import datetime
from app.config.database import mongo
from bson import ObjectId

class Goal:
    collection = mongo.db.goals

    @staticmethod
    def create(user_id, data):
        goal = {
            'user_id': user_id,
            'title': data.get('title'),
            'target_amount': float(data.get('target_amount', 0)),
            'current_amount': float(data.get('current_amount', 0)),
            'target_date': data.get('target_date', datetime.utcnow().strftime('%Y-%m-%d')),
            'created_at': datetime.utcnow()
        }
        result = Goal.collection.insert_one(goal)
        goal['_id'] = str(result.inserted_id)
        return goal

    @staticmethod
    def find_by_user(user_id):
        goals = list(Goal.collection.find({'user_id': user_id}))
        for g in goals:
            g['_id'] = str(g['_id'])
            if isinstance(g.get('created_at'), datetime):
                g['created_at'] = g['created_at'].isoformat()
        return goals

    @staticmethod
    def update(goal_id, user_id, data):
        goal = Goal.collection.find_one({'_id': ObjectId(goal_id), 'user_id': user_id})
        if not goal:
            return None

        update_data = {
            'title': data.get('title', goal['title']),
            'target_amount': float(data.get('target_amount', goal['target_amount'])),
            'current_amount': float(data.get('current_amount', goal['current_amount'])),
            'target_date': data.get('target_date', goal['target_date']),
            'updated_at': datetime.utcnow()
        }

        Goal.collection.update_one({'_id': ObjectId(goal_id)}, {'$set': update_data})
        updated_goal = Goal.collection.find_one({'_id': ObjectId(goal_id)})
        updated_goal['_id'] = str(updated_goal['_id'])
        return updated_goal

    @staticmethod
    def delete(goal_id, user_id):
        result = Goal.collection.delete_one({'_id': ObjectId(goal_id), 'user_id': user_id})
        return result.deleted_count > 0
