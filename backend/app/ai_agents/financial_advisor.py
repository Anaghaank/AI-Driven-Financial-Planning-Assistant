import os

class FinancialAdvisor:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        
        # Only initialize if API key is valid
        if self.api_key and self.api_key.startswith('sk-') and len(self.api_key) > 40:
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

        # START WITH FINANCIAL SNAPSHOT
        advice = f"""📊 Your Financial Snapshot:

    💰 Total Income: ₹{total_income:,.2f}
    💸 Total Expenses: ₹{total_expense:,.2f}
    💵 Net Savings: ₹{net_savings:,.2f}
    📈 Savings Rate: {savings_rate:.1f}%

    """

        # Add category breakdown if available
        if top_categories:
            advice += "🏷️ Top Spending Categories:\n"
            for cat, amount in top_categories:
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                advice += f"   • {cat}: ₹{amount:,.2f} ({percentage:.1f}%)\n"
            advice += "\n"

        # DYNAMIC RESPONSE BASED ON QUERY
        advice += "💡 Answer to Your Question:\n\n"

        if 'save' in query_lower or 'saving' in query_lower:
            if savings_rate >= 20:
                advice += f"Your savings rate of {savings_rate:.1f}% is excellent! Here's how to maximize it:\n\n"
                advice += "1. Consider investing your surplus in:\n"
                advice += "   • PPF (Public Provident Fund) for long-term tax-free returns\n"
                advice += "   • Mutual Funds (SIP) for wealth creation\n"
                advice += "   • Fixed Deposits for guaranteed returns\n\n"
                advice += "2. Diversify your investments across equity and debt\n"
                advice += "3. Take advantage of Section 80C deductions\n"
            else:
                advice += f"Your current savings rate is {savings_rate:.1f}%. Here's how to increase it:\n\n"
                advice += "1. Track every expense for 30 days to identify leaks\n"
                advice += "2. Apply the 50/30/20 rule:\n"
                advice += "   • 50% for needs (rent, food, utilities)\n"
                advice += "   • 30% for wants (entertainment, dining out)\n"
                advice += "   • 20% for savings and investments\n\n"
                if top_categories:
                    advice += f"3. Focus on reducing {top_categories[0][0]} expenses first (₹{top_categories[0][1]:,.2f})\n"
                advice += "4. Automate savings - transfer 20% of income immediately after salary\n"

        elif 'budget' in query_lower:
            advice += "📋 Budget Planning Strategy:\n\n"
            if total_income > 0:
                needs = total_income * 0.5
                wants = total_income * 0.3
                savings = total_income * 0.2
                advice += f"Based on ₹{total_income:,.2f} income:\n"
                advice += f"   • Needs (50%): ₹{needs:,.2f}\n"
                advice += f"   • Wants (30%): ₹{wants:,.2f}\n"
                advice += f"   • Savings (20%): ₹{savings:,.2f}\n\n"

            advice += "Steps to create your budget:\n"
            advice += "1. List all fixed expenses (rent, EMIs, utilities)\n"
            advice += "2. Set limits for variable expenses (food, entertainment)\n"
            advice += "3. Allocate for irregular expenses (festivals, gifts)\n"
            advice += "4. Review weekly and adjust monthly\n\n"

            if top_categories and top_categories[0][1] > total_expense * 0.4:
                advice += f"⚠️ Warning: {top_categories[0][0]} is {(top_categories[0][1]/total_expense*100):.0f}% of your budget!\n"
                advice += "Consider setting a strict limit for this category.\n"

        elif 'invest' in query_lower or 'investment' in query_lower:
            advice += "📈 Investment Recommendations for India:\n\n"
            advice += "Before investing, ensure you have:\n"
            advice += "1. Emergency fund (6 months expenses) ✓\n"
            advice += "2. Health insurance coverage ✓\n"
            advice += "3. Term life insurance ✓\n\n"

            advice += "Investment options based on time horizon:\n\n"
            advice += "Short-term (< 3 years):\n"
            advice += "   • Liquid Funds - 4-6% returns\n"
            advice += "   • Fixed Deposits - 6-7% returns\n"
            advice += "   • Recurring Deposits\n\n"

            advice += "Medium-term (3-5 years):\n"
            advice += "   • Debt Mutual Funds\n"
            advice += "   • Balanced Hybrid Funds\n"
            advice += "   • Gold (physical or digital)\n\n"

            advice += "Long-term (5+ years):\n"
            advice += "   • Equity Mutual Funds (SIP) - 12-15% average\n"
            advice += "   • PPF - 7.1% tax-free\n"
            advice += "   • NPS for retirement\n"
            advice += "   • Index Funds (Nifty 50, Sensex)\n"

        elif 'debt' in query_lower or 'loan' in query_lower or 'emi' in query_lower:
            advice += "💳 Debt Management Strategy:\n\n"
            advice += "1. List all debts with interest rates:\n"
            advice += "   • Credit cards (usually highest at 36-42%)\n"
            advice += "   • Personal loans (10-18%)\n"
            advice += "   • Home loans (8-10%)\n\n"

            advice += "2. Choose a repayment method:\n"
            advice += "   Avalanche Method: Pay highest interest first (saves money)\n"
            advice += "   Snowball Method: Pay smallest balance first (psychological wins)\n\n"

            advice += "3. Negotiate lower rates:\n"
            advice += "   • Call your credit card company for rate reduction\n"
            advice += "   • Consider balance transfer to 0% APR cards\n"
            advice += "   • Consolidate multiple loans\n\n"

            advice += "4. Pay more than minimum:\n"
            advice += "   • Even ₹1000 extra/month makes huge difference\n"
            advice += "   • Focus windfalls (bonus, gifts) on debt\n"

        elif 'tax' in query_lower:
            advice += "💰 Tax Saving Tips for India:\n\n"
            advice += "Section 80C (₹1.5 lakh limit):\n"
            advice += "   • PPF contributions\n"
            advice += "   • ELSS mutual funds\n"
            advice += "   • Life insurance premiums\n"
            advice += "   • Home loan principal repayment\n"
            advice += "   • Children's tuition fees\n\n"

            advice += "Additional Deductions:\n"
            advice += "   • 80D: Health insurance (₹25,000)\n"
            advice += "   • 80CCD(1B): NPS (₹50,000 extra)\n"
            advice += "   • 24(b): Home loan interest (₹2 lakh)\n"
            advice += "   • 80E: Education loan interest (no limit)\n\n"

            advice += "New Tax Regime vs Old:\n"
            advice += "Choose based on your deductions. Old regime better if you have many deductions.\n"

        elif 'emergency' in query_lower or 'fund' in query_lower:
            advice += "🚨 Emergency Fund Planning:\n\n"
            monthly_expenses = total_expense
            target_fund = monthly_expenses * 6

            advice += f"Your monthly expenses: ₹{monthly_expenses:,.2f}\n"
            advice += f"Target emergency fund: ₹{target_fund:,.2f} (6 months)\n\n"

            advice += "How to build it:\n"
            advice += "1. Start with ₹1,00,000 as initial goal\n"
            advice += "2. Save 10-15% of income monthly\n"
            advice += "3. Keep in liquid form:\n"
            advice += "   • Savings account (immediate access)\n"
            advice += "   • Liquid mutual funds (1-2 days)\n"
            advice += "   • Fixed deposits (penalty-free withdrawal)\n\n"

            advice += "Don't use it for:\n"
            advice += "   ❌ Vacations or shopping\n"
            advice += "   ❌ Regular expenses\n"
            advice += "   ✅ Only for true emergencies (job loss, medical)\n"
        
        elif 'retire' in query_lower or 'pension' in query_lower:
            advice += "👴 Retirement Planning:\n\n"
            advice += "Calculate how much you need:\n"
            advice += "1. Current monthly expenses: ₹{:,.0f}\n".format(total_expense)
            advice += "2. Inflation-adjusted (assume 6%/year)\n"
            advice += "3. Target corpus: 25-30x annual expenses\n\n"

            advice += "Best retirement instruments:\n"
            advice += "   • NPS (tax benefits + low cost)\n"
            advice += "   • PPF (tax-free + guaranteed)\n"
            advice += "   • Equity mutual funds (growth)\n"
            advice += "   • Employee PF (mandatory + safe)\n\n"
        
            advice += "Start early! A 25-year-old needs to save much less monthly than a 35-year-old for the same retirement corpus.\n"

        elif 'goal' in query_lower:
            advice += "🎯 Goal-Based Financial Planning:\n\n"
            advice += "Set SMART goals:\n"
            advice += "   • Specific: 'Save ₹5 lakhs' not 'Save money'\n"
            advice += "   • Measurable: Track monthly progress\n"
            advice += "   • Achievable: Realistic given your income\n"
            advice += "   • Relevant: Aligned with your life priorities\n"
            advice += "   • Time-bound: Set a deadline\n\n"

            advice += "Common financial goals:\n"
            advice += "1. Short-term (< 2 years): Emergency fund, vacation\n"
            advice += "2. Medium-term (2-5 years): Car, wedding, home down payment\n"
            advice += "3. Long-term (5+ years): House, child education, retirement\n\n"

            advice += "Match investments to goals:\n"
            advice += "   • Short-term → FD, Liquid funds\n"
            advice += "   • Medium-term → Debt funds, Balanced funds\n"
            advice += "   • Long-term → Equity funds, PPF, Real estate\n"

        else:
            # Default comprehensive advice
            advice += "Here's a comprehensive financial health check:\n\n"

            if savings_rate < 10:
                advice += "🚨 URGENT: Your savings rate is low\n"
                advice += f"Current: {savings_rate:.1f}% | Target: 20%+\n"
                advice += "Action: Cut discretionary spending by 10-15%\n\n"
            elif savings_rate < 20:
                advice += "⚠️ Your savings rate needs improvement\n"
                advice += f"Current: {savings_rate:.1f}% | Target: 20%+\n"
                advice += "Action: Review and optimize expenses\n\n"
            else:
                advice += "✅ Excellent savings rate!\n"
                advice += "Focus on investing wisely for wealth creation\n\n"

            if top_categories:
                advice += f"💸 Highest expense: {top_categories[0][0]} (₹{top_categories[0][1]:,.2f})\n"
                if top_categories[0][1] > total_expense * 0.4:
                    advice += "This seems high. Consider:\n"
                    advice += "   • Setting a strict monthly limit\n"
                    advice += "   • Finding cheaper alternatives\n"
                    advice += "   • Tracking daily spending in this category\n\n"

            advice += "📋 Quick Action Items:\n"
            advice += "1. Set up automatic savings transfer (20% of income)\n"
            advice += "2. Create category-wise monthly budgets\n"
            advice += "3. Review expenses weekly using this app\n"
            advice += "4. Start/increase SIP in mutual funds\n"
            advice += "5. Ensure adequate insurance coverage\n"


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