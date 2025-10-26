from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction

bp = Blueprint('transactions', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def get_transactions():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user)
        return jsonify(transactions), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('', methods=['POST'])
@jwt_required()
def create_transaction():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        transaction = Transaction.create(current_user, data)
        return jsonify(transaction), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    try:
        current_user = get_jwt_identity()
        analytics = Transaction.get_analytics(current_user)
        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    try:
        current_user = get_jwt_identity()
        deleted = Transaction.delete(transaction_id, current_user)
        if deleted:
            return jsonify({'message': 'Transaction deleted successfully'}), 200
        return jsonify({'error': 'Transaction not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500