import sys
import os

# Test without database
from app.ai_agents.financial_advisor import FinancialAdvisor

# Test advisor directly
advisor = FinancialAdvisor(os.getenv('OPENAI_API_KEY'))

# Create sample transactions
sample_transactions = [
    {'amount': 5000, 'type': 'income', 'category': 'Salary'},
    {'amount': 1000, 'type': 'expense', 'category': 'Food & Groceries'},
    {'amount': 500, 'type': 'expense', 'category': 'Transportation'},
    {'amount': 800, 'type': 'expense', 'category': 'Shopping'},
    {'amount': 300, 'type': 'expense', 'category': 'Entertainment'},
]

print("=" * 60)
print("TESTING AI INSIGHTS")
print("=" * 60)
insights = advisor.analyze_spending(sample_transactions)
print(insights)
print("\n")

print("=" * 60)
print("TESTING AI ADVICE")
print("=" * 60)
advice = advisor.get_advice("How can I save more money?", sample_transactions)
print(advice)
print("\n")

print("=" * 60)
print("TEST COMPLETED SUCCESSFULLY!")
print("=" * 60)