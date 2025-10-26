from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.ml_models.expense_predictor import ExpensePredictor
from app.ai_agents.financial_advisor import FinancialAdvisor
from app.models.transaction import Transaction
import os

bp = Blueprint('ai', __name__)

predictor = ExpensePredictor()
advisor = FinancialAdvisor(os.getenv('OPENAI_API_KEY'))

@bp.route('/predictions', methods=['GET'])
@jwt_required()
def get_predictions():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user)
        
        if len(transactions) < 10:
            return jsonify({'message': 'Not enough data for predictions'}), 200
        
        predictions = predictor.predict_simple(transactions)
        return jsonify(predictions), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/advice', methods=['POST'])
@jwt_required()
def get_advice():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        query = data.get('query', '')
        
        # Get user context
        transactions = Transaction.find_by_user(current_user, limit=50)
        
        advice = advisor.get_advice(query, transactions)
        return jsonify({'advice': advice}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/insights', methods=['GET'])
@jwt_required()
def get_insights():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user)
        
        insights = advisor.analyze_spending(transactions)
        return jsonify({'insights': insights}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500