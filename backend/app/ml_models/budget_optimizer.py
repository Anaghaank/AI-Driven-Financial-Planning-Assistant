import numpy as np
from datetime import datetime, timedelta

class BudgetOptimizer:
    def __init__(self):
        self.category_limits = {
            'Food & Groceries': 0.20,      # 20% of income
            'Transportation': 0.10,         # 10% of income
            'Bills': 0.15,                  # 15% of income
            'Shopping': 0.10,               # 10% of income
            'Entertainment': 0.05,          # 5% of income
            'Healthcare': 0.05,             # 5% of income
        }
    
    def analyze_spending_pattern(self, transactions):
        """Analyze spending patterns and suggest budget"""
        # Calculate total income and expenses
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        
        # Group by category
        category_spending = {}
        for t in transactions:
            if t['type'] == 'expense':
                cat = t.get('category', 'Other')
                category_spending[cat] = category_spending.get(cat, 0) + t['amount']
        
        # Calculate recommended budgets
        recommendations = {}
        for category, limit_percent in self.category_limits.items():
            recommended = total_income * limit_percent
            actual = category_spending.get(category, 0)
            
            recommendations[category] = {
                'recommended': recommended,
                'actual': actual,
                'difference': recommended - actual,
                'status': 'under' if actual < recommended else 'over',
                'percentage': (actual / total_income * 100) if total_income > 0 else 0
            }
        
        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'recommendations': recommendations,
            'savings_potential': sum(r['difference'] for r in recommendations.values() if r['difference'] > 0)
        }
    
    def get_smart_suggestions(self, transactions):
        """Generate AI-powered suggestions"""
        analysis = self.analyze_spending_pattern(transactions)
        suggestions = []
        
        for category, data in analysis['recommendations'].items():
            if data['status'] == 'over' and data['actual'] > 0:
                overspend = abs(data['difference'])
                suggestions.append({
                    'category': category,
                    'type': 'warning',
                    'message': f"You're overspending on {category} by ₹{overspend:.2f}",
                    'action': f"Try to reduce {category} expenses by {((overspend/data['actual'])*100):.0f}%"
                })
        
        # Savings suggestion
        if analysis['savings_potential'] > 0:
            suggestions.append({
                'category': 'Savings',
                'type': 'opportunity',
                'message': f"You can save up to ₹{analysis['savings_potential']:.2f} more per month",
                'action': "Consider investing this in mutual funds or fixed deposits"
            })
        
        return suggestions