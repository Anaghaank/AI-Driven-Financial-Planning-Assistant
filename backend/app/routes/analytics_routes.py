from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.ml_models.budget_optimizer import BudgetOptimizer
from datetime import datetime, timedelta
import calendar

bp = Blueprint('analytics', __name__)

@bp.route('/spending-trends', methods=['GET'])
@jwt_required()
def get_spending_trends():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user, limit=1000)
        
        # Group by month
        monthly_data = {}
        for txn in transactions:
            try:
                date = datetime.fromisoformat(txn['date'].replace('Z', '+00:00'))
                month_key = f"{date.year}-{date.month:02d}"
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'month': calendar.month_name[date.month],
                        'year': date.year,
                        'income': 0,
                        'expense': 0,
                        'categories': {}
                    }
                
                if txn['type'] == 'income':
                    monthly_data[month_key]['income'] += txn['amount']
                else:
                    monthly_data[month_key]['expense'] += txn['amount']
                    cat = txn.get('category', 'Other')
                    monthly_data[month_key]['categories'][cat] = \
                        monthly_data[month_key]['categories'].get(cat, 0) + txn['amount']
            except:
                continue
        
        # Sort by date
        sorted_data = sorted(monthly_data.items(), key=lambda x: x[0])
        result = [data for _, data in sorted_data[-12:]]  # Last 12 months
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/budget-recommendations', methods=['GET'])
@jwt_required()
def get_budget_recommendations():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user, limit=500)
        
        optimizer = BudgetOptimizer()
        analysis = optimizer.analyze_spending_pattern(transactions)
        suggestions = optimizer.get_smart_suggestions(transactions)
        
        return jsonify({
            'analysis': analysis,
            'suggestions': suggestions
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/financial-health-score', methods=['GET'])
@jwt_required()
def get_financial_health_score():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user, limit=500)
        
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        
        if total_income == 0:
            return jsonify({'score': 0, 'grade': 'N/A', 'message': 'No income data'}), 200
        
        # Calculate score (0-100)
        savings_rate = (total_income - total_expense) / total_income
        
        score = 0
        factors = []
        
        # Savings rate (40 points)
        if savings_rate >= 0.30:
            score += 40
            factors.append({'name': 'Savings Rate', 'points': 40, 'status': 'Excellent'})
        elif savings_rate >= 0.20:
            score += 30
            factors.append({'name': 'Savings Rate', 'points': 30, 'status': 'Good'})
        elif savings_rate >= 0.10:
            score += 20
            factors.append({'name': 'Savings Rate', 'points': 20, 'status': 'Fair'})
        else:
            score += 10
            factors.append({'name': 'Savings Rate', 'points': 10, 'status': 'Poor'})
        
        # Transaction tracking (20 points)
        if len(transactions) > 50:
            score += 20
            factors.append({'name': 'Regular Tracking', 'points': 20, 'status': 'Excellent'})
        elif len(transactions) > 20:
            score += 15
            factors.append({'name': 'Regular Tracking', 'points': 15, 'status': 'Good'})
        else:
            score += 10
            factors.append({'name': 'Regular Tracking', 'points': 10, 'status': 'Fair'})
        
        # Category diversification (20 points)
        categories = set(t.get('category') for t in transactions if t['type'] == 'expense')
        if len(categories) >= 5:
            score += 20
            factors.append({'name': 'Expense Categories', 'points': 20, 'status': 'Diverse'})
        elif len(categories) >= 3:
            score += 15
            factors.append({'name': 'Expense Categories', 'points': 15, 'status': 'Moderate'})
        else:
            score += 10
            factors.append({'name': 'Expense Categories', 'points': 10, 'status': 'Limited'})
        
        # Budget adherence (20 points)
        optimizer = BudgetOptimizer()
        analysis = optimizer.analyze_spending_pattern(transactions)
        overspending_count = sum(1 for r in analysis['recommendations'].values() if r['status'] == 'over')
        
        if overspending_count == 0:
            score += 20
            factors.append({'name': 'Budget Control', 'points': 20, 'status': 'Excellent'})
        elif overspending_count <= 2:
            score += 15
            factors.append({'name': 'Budget Control', 'points': 15, 'status': 'Good'})
        else:
            score += 10
            factors.append({'name': 'Budget Control', 'points': 10, 'status': 'Needs Improvement'})
        
        # Determine grade
        if score >= 80:
            grade = 'A'
            message = 'Excellent financial health!'
        elif score >= 60:
            grade = 'B'
            message = 'Good financial health with room for improvement'
        elif score >= 40:
            grade = 'C'
            message = 'Fair financial health, focus on savings'
        else:
            grade = 'D'
            message = 'Needs significant improvement'
        
        return jsonify({
            'score': score,
            'grade': grade,
            'message': message,
            'factors': factors,
            'savings_rate': savings_rate * 100
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@bp.route('/savings-suggestions', methods=['GET'])
@jwt_required()
def get_savings_suggestions():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user, limit=500)
        
        # Analyze spending patterns
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        
        # Category spending
        category_spending = {}
        for t in transactions:
            if t['type'] == 'expense':
                cat = t.get('category', 'Other')
                category_spending[cat] = category_spending.get(cat, 0) + t['amount']
        
        suggestions = []
        
        # Analyze each category
        for category, amount in sorted(category_spending.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total_expense * 100) if total_expense > 0 else 0
            
            if category == 'Food & Groceries' and percentage > 25:
                suggestions.append({
                    'category': category,
                    'current_spend': amount,
                    'potential_saving': amount * 0.2,  # 20% reduction
                    'tip': 'Cook at home more often, buy in bulk, use grocery apps for discounts',
                    'priority': 'high'
                })
            
            elif category == 'Transportation' and percentage > 15:
                suggestions.append({
                    'category': category,
                    'current_spend': amount,
                    'potential_saving': amount * 0.15,
                    'tip': 'Use public transport, carpool, consider monthly passes',
                    'priority': 'medium'
                })
            
            elif category == 'Shopping' and percentage > 15:
                suggestions.append({
                    'category': category,
                    'current_spend': amount,
                    'potential_saving': amount * 0.3,
                    'tip': 'Wait 24 hours before impulse purchases, use cashback apps, compare prices',
                    'priority': 'high'
                })
            
            elif category == 'Entertainment' and percentage > 10:
                suggestions.append({
                    'category': category,
                    'current_spend': amount,
                    'potential_saving': amount * 0.25,
                    'tip': 'Share subscriptions, look for free alternatives, limit dining out',
                    'priority': 'medium'
                })
        
        # Calculate total potential savings
        total_potential = sum(s['potential_saving'] for s in suggestions)
        
        return jsonify({
            'suggestions': suggestions,
            'total_potential_savings': total_potential,
            'annual_potential': total_potential * 12
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user, limit=500)
        
        from app.ml_models.alert_system import AlertSystem
        alert_system = AlertSystem()
        alerts = alert_system.analyze_transactions(transactions)
        
        return jsonify(alerts), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500