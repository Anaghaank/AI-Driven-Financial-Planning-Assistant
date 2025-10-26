import os

class FinancialAdvisor:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        # Only initialize if API key is provided and not placeholder
        if self.api_key and self.api_key != 'your-openai-api-key-here' and len(self.api_key) > 20:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.client = None
    
    def get_advice(self, query, transactions):
        """Get financial advice using OpenAI"""
        if not self.client:
            return self._get_fallback_advice(query, transactions)
        
        try:
            # Calculate summary
            total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
            total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
            
            context = f"""
            User's Financial Summary:
            - Total Expenses: ${total_expense:.2f}
            - Total Income: ${total_income:.2f}
            - Number of Transactions: {len(transactions)}
            
            Question: {query}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful financial advisor. Provide clear, actionable advice in 2-3 paragraphs."},
                    {"role": "user", "content": context}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error getting AI advice: {e}")
            return self._get_fallback_advice(query, transactions)
    
    def _get_fallback_advice(self, query, transactions):
        """Fallback advice when API is not available"""
        if not transactions or len(transactions) == 0:
            return """Welcome to your Financial Assistant!

Start by adding some transactions to get personalized insights and recommendations.

Here are some tips to get started:
1. Track all your income and expenses
2. Categorize transactions accurately
3. Set realistic financial goals
4. Review your spending weekly

For AI-powered personalized advice, add your OpenAI API key to the backend .env file."""

        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
        
        return f"""Based on your financial data:

Your current savings rate is {savings_rate:.1f}%. Financial experts recommend saving at least 20% of your income.

Total Income: ${total_income:.2f}
Total Expenses: ${total_expense:.2f}
Net Savings: ${total_income - total_expense:.2f}

Recommendations:
1. {"Great job! Keep up the good savings rate." if savings_rate >= 20 else "Try to increase your savings rate by reducing non-essential expenses."}
2. Track your largest expense categories and look for areas to cut back
3. Set specific financial goals to stay motivated
4. Review your spending patterns weekly to stay on track

For more personalized AI-powered advice, please add your OpenAI API key to the .env file."""
    
    def analyze_spending(self, transactions):
        """Analyze spending patterns"""
        if not transactions or len(transactions) == 0:
            return "Add transactions to see your spending analysis!"
        
        # Group by category
        categories = {}
        total_expense = 0
        
        for t in transactions:
            if t['type'] == 'expense':
                cat = t.get('category', 'Other')
                categories[cat] = categories.get(cat, 0) + t['amount']
                total_expense += t['amount']
        
        if total_expense == 0:
            return "No expenses recorded yet. Add some expense transactions to see analysis."
        
        # Find top categories
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        insights = "Your spending breakdown:\n\n"
        for cat, amount in sorted_cats[:5]:
            percentage = (amount / total_expense * 100)
            insights += f"• {cat}: ${amount:.2f} ({percentage:.1f}%)\n"
        
        # Add insights
        insights += f"\nTotal Expenses: ${total_expense:.2f}\n"
        
        if sorted_cats:
            top_category, top_amount = sorted_cats[0]
            insights += f"\n💡 Insight: {top_category} is your largest expense category at ${top_amount:.2f}. Consider if there are opportunities to reduce spending here."
        
        return insights