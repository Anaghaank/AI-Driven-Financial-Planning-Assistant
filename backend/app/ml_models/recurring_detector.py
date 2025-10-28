from datetime import datetime, timedelta
from collections import defaultdict
import re

class RecurringDetector:
    def __init__(self):
        self.similarity_threshold = 0.8
    
    def calculate_similarity(self, str1, str2):
        """Calculate similarity between two strings"""
        # Simple similarity based on common words
        words1 = set(re.findall(r'\w+', str1.lower()))
        words2 = set(re.findall(r'\w+', str2.lower()))
        
        if not words1 or not words2:
            return 0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def detect_recurring(self, transactions):
        """Detect recurring transactions"""
        # Group transactions by similar description and amount
        groups = defaultdict(list)
        
        for txn in transactions:
            if txn['type'] != 'expense':
                continue
            
            # Round amount to group similar transactions
            amount_key = round(txn['amount'], -1)  # Round to nearest 10
            
            # Find similar transactions
            found_group = False
            for key in list(groups.keys()):
                if abs(key[1] - amount_key) <= 50:  # Within ₹50
                    # Check description similarity
                    for existing_txn in groups[key]:
                        similarity = self.calculate_similarity(
                            txn['description'], 
                            existing_txn['description']
                        )
                        if similarity >= self.similarity_threshold:
                            groups[key].append(txn)
                            found_group = True
                            break
                if found_group:
                    break
            
            if not found_group:
                key = (txn['description'][:20], amount_key)
                groups[key].append(txn)
        
        # Find recurring patterns (3+ occurrences)
        recurring = []
        for key, txns in groups.items():
            if len(txns) >= 3:
                # Calculate frequency
                dates = [datetime.fromisoformat(t['date'].replace('Z', '+00:00')) for t in txns]
                dates.sort()
                
                if len(dates) >= 2:
                    avg_days = sum((dates[i+1] - dates[i]).days for i in range(len(dates)-1)) / (len(dates)-1)
                    
                    recurring.append({
                        'description': txns[0]['description'],
                        'category': txns[0]['category'],
                        'avg_amount': sum(t['amount'] for t in txns) / len(txns),
                        'frequency': f"Every {int(avg_days)} days",
                        'occurrences': len(txns),
                        'last_date': dates[-1].strftime('%d-%m-%Y'),
                        'next_expected': (dates[-1] + timedelta(days=int(avg_days))).strftime('%d-%m-%Y')
                    })
        
        return sorted(recurring, key=lambda x: x['avg_amount'], reverse=True)