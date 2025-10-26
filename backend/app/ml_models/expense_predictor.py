import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ExpensePredictor:
    def __init__(self):
        self.model = None
    
    def predict_simple(self, transactions):
        """Simple moving average prediction"""
        if len(transactions) < 7:
            return {'next_month': 0, 'confidence': 'low'}
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        df['amount'] = pd.to_numeric(df['amount'])
        
        # Calculate average of last 30 days
        recent = df.head(30)
        avg_expense = recent[recent['type'] == 'expense']['amount'].sum() / 30 * 30
        
        return {
            'next_month_prediction': round(avg_expense, 2),
            'daily_average': round(avg_expense / 30, 2),
            'confidence': 'medium',
            'based_on_days': len(recent)
        }