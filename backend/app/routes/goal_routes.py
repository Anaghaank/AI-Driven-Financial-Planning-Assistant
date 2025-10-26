from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.goal import Goal

bp = Blueprint('goals', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def get_goals():
    try:
        current_user = get_jwt_identity()
        goals = Goal.find_by_user(current_user)
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

@bp.route('/<goal_id>', methods=['PUT'])
@jwt_required()
def update_goal(goal_id):
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        # Add update logic here
        return jsonify({'message': 'Goal updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    try:
        current_user = get_jwt_identity()
        # Add delete logic here
        return jsonify({'message': 'Goal deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500