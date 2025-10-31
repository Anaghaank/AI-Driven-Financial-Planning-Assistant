from datetime import datetime, timedelta

class AlertSystem:
    def __init__(self):
        self.alert_thresholds = {
            'high_spending': 1.5,  # 50% above average
            'unusual_category': 2.0,  # 2x normal spending
            'daily_limit': 5000,  # Daily spending limit
        }
    
    def analyze_transactions(self, transactions):
        """Generate alerts based on spending patterns"""
        alerts = []
        
        if not transactions:
            return alerts
        
        # Calculate averages
        daily_spending = {}
        category_spending = {}
        
        for txn in transactions:
            if txn['type'] == 'expense':
                # Daily spending
                date = datetime.fromisoformat(txn['date'].replace('Z', '+00:00')).date()
                daily_spending[date] = daily_spending.get(date, 0) + txn['amount']
                
                # Category spending
                cat = txn.get('category', 'Other')
                category_spending[cat] = category_spending.get(cat, 0) + txn['amount']
        
        # Check for high daily spending
        if daily_spending:
            avg_daily = sum(daily_spending.values()) / len(daily_spending)
            
            for date, amount in daily_spending.items():
                if amount > avg_daily * self.alert_thresholds['high_spending']:
                    alerts.append({
                        'type': 'high_spending',
                        'severity': 'warning',
                        'date': date.isoformat(),
                        'message': f'High spending detected on {date.strftime("%d %b")}: ₹{amount:.2f}',
                        'suggestion': 'Review your expenses for this day and identify unnecessary purchases'
                    })
        
        # Check for unusual category spending
        if len(transactions) > 30:  # Need enough data
            for cat, total in category_spending.items():
                avg_per_transaction = total / len([t for t in transactions if t.get('category') == cat])
                
                # Find recent large transactions in this category
                recent_transactions = [
                    t for t in transactions 
                    if t.get('category') == cat 
                    and (datetime.utcnow() - datetime.fromisoformat(t['date'].replace('Z', '+00:00'))).days <= 7
                ]
                
                for txn in recent_transactions:
                    if txn['amount'] > avg_per_transaction * self.alert_thresholds['unusual_category']:
                        alerts.append({
                            'type': 'unusual_transaction',
                            'severity': 'info',
                            'category': cat,
                            'amount': txn['amount'],
                            'message': f'Large {cat} expense: ₹{txn["amount"]:.2f}',
                            'suggestion': 'Was this expected? Consider if this could be reduced next time'
                        })
        
        return alerts