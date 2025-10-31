from datetime import datetime
from app.config.database import mongo
from bson import ObjectId

class Goal:
    collection = mongo.db.goals
    
    @staticmethod
    def create(user_id, data):
        goal = {
            'user_id': user_id,
            'name': data['name'],
            'target_amount': float(data['target_amount']),
            'current_amount': float(data.get('current_amount', 0)),
            'deadline': data.get('deadline'),
            'linked_bank_id': data.get('linked_bank_id'),  # Link to specific bank
            'auto_track': data.get('auto_track', False),   # Auto-track from savings
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = Goal.collection.insert_one(goal)
        goal['_id'] = str(result.inserted_id)
        return goal
    
    @staticmethod
    def find_by_user(user_id):
        goals = list(Goal.collection.find({'user_id': user_id}))
        for g in goals:
            g['_id'] = str(g['_id'])
            target = g.get('target_amount', 1)
            current = g.get('current_amount', 0)
            g['progress'] = (current / target * 100) if target > 0 else 0
            
            # Calculate time remaining
            if g.get('deadline'):
                try:
                    if isinstance(g['deadline'], str):
                        from dateutil import parser
                        deadline = parser.parse(g['deadline'])
                    else:
                        deadline = g['deadline']
                    
                    days_remaining = (deadline - datetime.utcnow()).days
                    g['days_remaining'] = max(0, days_remaining)
                except:
                    g['days_remaining'] = None
        
        return goals
    
    @staticmethod
    def update(goal_id, user_id, data):
        data['updated_at'] = datetime.utcnow()
        Goal.collection.update_one(
            {'_id': ObjectId(goal_id), 'user_id': user_id},
            {'$set': data}
        )
        goal = Goal.collection.find_one({'_id': ObjectId(goal_id)})
        if goal:
            goal['_id'] = str(goal['_id'])
        return goal
    
    @staticmethod
    def add_progress(goal_id, user_id, amount):
        """Add progress to goal"""
        goal = Goal.collection.find_one({'_id': ObjectId(goal_id), 'user_id': user_id})
        if not goal:
            return None
        
        new_amount = goal.get('current_amount', 0) + amount
        
        return Goal.update(goal_id, user_id, {'current_amount': new_amount})
    
    @staticmethod
    def delete(goal_id, user_id):
        result = Goal.collection.delete_one({'_id': ObjectId(goal_id), 'user_id': user_id})
        return result.deleted_count > 0