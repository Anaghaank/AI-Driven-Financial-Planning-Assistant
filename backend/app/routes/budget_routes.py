from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.budget import Budget

bp = Blueprint('budgets', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def get_budgets():
    try:
        current_user = get_jwt_identity()
        budgets = Budget.find_by_user(current_user)
        return jsonify(budgets), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('', methods=['POST'])
@jwt_required()
def create_budget():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        budget = Budget.create(current_user, data)
        return jsonify(budget), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<budget_id>', methods=['PUT'])
@jwt_required()
def update_budget(budget_id):
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        # Add update logic here
        return jsonify({'message': 'Budget updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<budget_id>', methods=['DELETE'])
@jwt_required()
def delete_budget(budget_id):
    try:
        current_user = get_jwt_identity()
        # Add delete logic here
        return jsonify({'message': 'Budget deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500