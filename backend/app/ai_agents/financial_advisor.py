import os

class FinancialAdvisor:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        
        # Only initialize if API key is valid
        if self.api_key and self.api_key != 'your-openai-api-key-here' and len(self.api_key) > 20:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                print("OpenAI client initialized successfully")
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.client = None
        else:
            print("OpenAI API key not configured - using fallback advice")
    
    def get_advice(self, query, transactions):
        """Get financial advice using OpenAI or fallback"""
        print(f"Getting advice - OpenAI available: {self.client is not None}")
        
        if not self.client:
            return self._get_fallback_advice(query, transactions)
        
        try:
            # Calculate summary
            total_expense = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense')
            total_income = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'income')
            
            # Get category breakdown
            categories = {}
            for t in transactions:
                if t.get('type') == 'expense':
                    cat = t.get('category', 'Other')
                    categories[cat] = categories.get(cat, 0) + t.get('amount', 0)
            
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            category_text = ", ".join([f"{cat}: ${amt:.2f}" for cat, amt in top_categories])
            
            context = f"""
            User's Financial Summary:
            - Total Income: ${total_income:.2f}
            - Total Expenses: ${total_expense:.2f}
            - Net Savings: ${total_income - total_expense:.2f}
            - Savings Rate: {((total_income - total_expense) / total_income * 100) if total_income > 0 else 0:.1f}%
            - Number of Transactions: {len(transactions)}
            - Top Expense Categories: {category_text if category_text else "None"}
            
            User Question: {query}
            
            Please provide specific, actionable financial advice in 2-3 short paragraphs.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful personal financial advisor. Provide clear, practical advice tailored to the user's specific financial situation."},
                    {"role": "user", "content": context}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._get_fallback_advice(query, transactions)
    
    def _get_fallback_advice(self, query, transactions):
        """Fallback advice when OpenAI is not available"""
        if not transactions or len(transactions) == 0:
            return """Welcome to your Financial Assistant! 👋

I can help you with your finances once you add some transactions. Here's how to get started:

📊 Track Your Money:
- Add your income sources (salary, freelance, investments)
- Record all expenses (categorize them accurately)
- Be consistent - track daily for best insights

💡 General Financial Tips:
- Follow the 50/30/20 rule: 50% needs, 30% wants, 20% savings
- Build an emergency fund with 3-6 months of expenses
- Pay yourself first - automate your savings
- Review your spending weekly to stay on track

Ask me questions like:
"How can I save more money?"
"What's my biggest expense category?"
"How much should I save each month?"

Start adding transactions to get personalized advice! 🚀"""

        # Calculate financial metrics
        total_expense = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense')
        total_income = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'income')
        net_savings = total_income - total_expense
        savings_rate = ((net_savings / total_income * 100) if total_income > 0 else 0)
        
        # Get category breakdown
        categories = {}
        for t in transactions:
            if t.get('type') == 'expense':
                cat = t.get('category', 'Other')
                categories[cat] = categories.get(cat, 0) + t.get('amount', 0)
        
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Generate contextual advice based on query keywords
        query_lower = query.lower()
        
        advice = f"""📊 Your Financial Snapshot:

💰 Total Income: ${total_income:.2f}
💸 Total Expenses: ${total_expense:.2f}
💵 Net Savings: ${net_savings:.2f}
📈 Savings Rate: {savings_rate:.1f}%

"""
        
        # Add category breakdown if available
        if top_categories:
            advice += "🏷️ Top Spending Categories:\n"
            for cat, amount in top_categories:
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                advice += f"   • {cat}: ${amount:.2f} ({percentage:.1f}%)\n"
            advice += "\n"
        
        # Contextual advice based on query
        if 'save' in query_lower or 'saving' in query_lower:
            if savings_rate >= 20:
                advice += "✅ Great job! Your savings rate of {:.1f}% is excellent. Consider investing surplus funds for long-term growth.\n\n".format(savings_rate)
            else:
                advice += "💡 Your savings rate is {:.1f}%. Aim for at least 20%. Try these strategies:\n".format(savings_rate)
                advice += "   • Reduce spending in your top expense categories\n"
                advice += "   • Automate savings transfers right after payday\n"
                advice += "   • Use the 24-hour rule for non-essential purchases\n\n"
        
        elif 'budget' in query_lower:
            advice += "📋 Budget Recommendations:\n"
            advice += "   • Apply the 50/30/20 rule: 50% needs, 30% wants, 20% savings\n"
            advice += "   • Set spending limits for each category\n"
            advice += "   • Review and adjust your budget monthly\n"
            if top_categories:
                advice += f"   • Focus on reducing {top_categories[0][0]} expenses first\n\n"
        
        elif 'debt' in query_lower:
            advice += "💳 Debt Management Tips:\n"
            advice += "   • List all debts with interest rates\n"
            advice += "   • Use avalanche method (highest interest first) or snowball (smallest balance first)\n"
            advice += "   • Try to pay more than minimum payments\n"
            advice += "   • Consider debt consolidation if rates are high\n\n"
        
        elif 'invest' in query_lower:
            advice += "📈 Investment Guidance:\n"
            advice += "   • Build emergency fund first (3-6 months expenses)\n"
            advice += "   • Max out employer 401(k) match if available\n"
            advice += "   • Consider low-cost index funds for long-term growth\n"
            advice += "   • Diversify across asset classes\n\n"
        
        else:
            # General advice
            advice += "💡 Personalized Recommendations:\n\n"
            
            if savings_rate < 10:
                advice += "🚨 Priority: Increase your savings rate\n"
                advice += "   • Current: {:.1f}% | Target: 20%+\n".format(savings_rate)
                advice += "   • Review discretionary spending\n\n"
            
            if top_categories and top_categories[0][1] > total_expense * 0.4:
                advice += f"⚠️ {top_categories[0][0]} is {(top_categories[0][1]/total_expense*100):.0f}% of expenses\n"
                advice += "   • Look for ways to reduce this category\n\n"
            
            advice += "✨ Quick Wins:\n"
            advice += "   • Track expenses daily for awareness\n"
            advice += "   • Set up automatic savings transfers\n"
            advice += "   • Use cash for discretionary spending\n"
            advice += "   • Review subscriptions and cancel unused ones\n"
        
        advice += "\n💬 For AI-powered personalized advice, add your OpenAI API key to backend/.env"
        
        return advice
    
    def analyze_spending(self, transactions):
        """Analyze spending patterns"""
        if not transactions or len(transactions) == 0:
            return "📊 Start tracking your transactions to see detailed spending analysis here!"
        
        # Group by category
        categories = {}
        total_expense = 0
        total_income = 0
        
        for t in transactions:
            amount = t.get('amount', 0)
            if t.get('type') == 'expense':
                cat = t.get('category', 'Other')
                categories[cat] = categories.get(cat, 0) + amount
                total_expense += amount
            elif t.get('type') == 'income':
                total_income += amount
        
        if total_expense == 0:
            return "💰 No expenses recorded yet. Add some transactions to see your spending breakdown!"
        
        # Find top categories
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        insights = "📊 Your Spending Analysis:\n\n"
        insights += f"💸 Total Expenses: ${total_expense:.2f}\n"
        insights += f"💰 Total Income: ${total_income:.2f}\n"
        insights += f"💵 Net: ${total_income - total_expense:.2f}\n\n"
        
        insights += "🏷️ Spending Breakdown:\n"
        for i, (cat, amount) in enumerate(sorted_cats[:5], 1):
            percentage = (amount / total_expense * 100)
            bar_length = int(percentage / 5)
            bar = "█" * bar_length
            insights += f"{i}. {cat}: ${amount:.2f} ({percentage:.1f}%)\n"
            insights += f"   {bar}\n"
        
        # Add insights based on data
        insights += "\n💡 Insights:\n"
        
        if sorted_cats:
            top_category, top_amount = sorted_cats[0]
            top_percentage = (top_amount / total_expense * 100)
            
            if top_percentage > 40:
                insights += f"• {top_category} dominates your spending at {top_percentage:.0f}%\n"
                insights += "  Consider if there are opportunities to reduce this.\n"
            else:
                insights += f"• Your spending is relatively balanced\n"
        
        savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
        
        if savings_rate >= 20:
            insights += f"• Excellent! You're saving {savings_rate:.1f}% of income\n"
        elif savings_rate >= 10:
            insights += f"• Good progress at {savings_rate:.1f}% savings rate\n"
            insights += "  Try to increase it to 20%\n"
        else:
            insights += f"• Your savings rate is {savings_rate:.1f}%\n"
            insights += "  Aim to increase it to at least 20%\n"
        
        return insights