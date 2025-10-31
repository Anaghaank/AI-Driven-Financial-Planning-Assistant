from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.goal import Goal
from app.models.bank import Bank

bp = Blueprint('goals', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def get_goals():
    try:
        current_user = get_jwt_identity()
        goals = Goal.find_by_user(current_user)
        
        # Add bank info if linked
        banks = {b['_id']: b for b in Bank.find_by_user(current_user)}
        
        for goal in goals:
            if goal.get('linked_bank_id') and goal['linked_bank_id'] in banks:
                goal['linked_bank'] = banks[goal['linked_bank_id']]
        
        return jsonify(goals), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('', methods=['POST'])
@jwt_required()
def create_goal():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        goal = Goal.create(current_user, data)
        return jsonify(goal), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<goal_id>/add-progress', methods=['POST'])
@jwt_required()
def add_goal_progress(goal_id):
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        goal = Goal.add_progress(goal_id, current_user, amount)
        
        if not goal:
            return jsonify({'error': 'Goal not found'}), 404
        
        return jsonify(goal), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        goal = Goal.update(goal_id, current_user, data)
        if goal:
            return jsonify(goal), 200
        return jsonify({'error': 'Goal not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    try:
        current_user = get_jwt_identity()
        deleted = Goal.delete(goal_id, current_user)
        if deleted:
            return jsonify({'message': 'Goal deleted successfully'}), 200
        return jsonify({'error': 'Goal not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500