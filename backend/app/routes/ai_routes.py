from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.ml_models.expense_predictor import ExpensePredictor
from app.ai_agents.financial_advisor import FinancialAdvisor
from app.models.transaction import Transaction
import os

bp = Blueprint('ai', __name__)

# Initialize predictor and advisor
predictor = ExpensePredictor()
advisor = FinancialAdvisor(os.getenv('OPENAI_API_KEY'))

@bp.route('/predictions', methods=['GET'])
@jwt_required()
def get_predictions():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user)
        
        if len(transactions) < 7:
            return jsonify({
                'message': 'Not enough data for predictions',
                'next_month_prediction': 0,
                'daily_average': 0,
                'confidence': 'low',
                'based_on_days': len(transactions)
            }), 200
        
        predictions = predictor.predict_simple(transactions)
        return jsonify(predictions), 200
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return jsonify({
            'message': 'Predictions unavailable',
            'next_month_prediction': 0,
            'daily_average': 0,
            'confidence': 'low',
            'based_on_days': 0
        }), 200

@bp.route('/advice', methods=['POST'])
@jwt_required()
def get_advice():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'advice': 'Please provide a question.'}), 400
        
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'advice': 'Please ask a specific question about your finances.'}), 200
        
        # Get user context
        transactions = Transaction.find_by_user(current_user, limit=100)
        
        print(f"Getting advice for query: {query}")
        print(f"Number of transactions: {len(transactions)}")
        
        advice = advisor.get_advice(query, transactions)
        
        print(f"Advice generated: {advice[:100]}...")
        
        return jsonify({'advice': advice}), 200
    except Exception as e:
        print(f"Advice error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return fallback advice
        return jsonify({
            'advice': '''I'm here to help with your finances!

Here are some general tips:
1. Track all income and expenses regularly
2. Aim to save at least 20% of your income
3. Create an emergency fund covering 3-6 months of expenses
4. Review and categorize your transactions weekly
5. Set specific, measurable financial goals

Ask me specific questions like:
- "How can I save more money?"
- "What are my biggest expenses?"
- "How can I improve my budget?"
- "Should I focus on saving or paying off debt?"'''
        }), 200

@bp.route('/insights', methods=['GET'])
@jwt_required()
def get_insights():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user)
        
        print(f"Getting insights for {len(transactions)} transactions")
        
        insights = advisor.analyze_spending(transactions)
        
        print(f"Insights generated: {insights[:100]}...")
        
        return jsonify({'insights': insights}), 200
    except Exception as e:
        print(f"Insights error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'insights': 'Add transactions to see your personalized spending insights!'
        }), 200