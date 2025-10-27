import pdfplumber
import re
from datetime import datetime
from dateutil import parser
import hashlib

class StatementExtractor:
    def __init__(self):
        self.date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'[A-Za-z]{3}\s+\d{1,2},?\s+\d{4}'
        ]
        
        self.amount_pattern = r'\$?\s*-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
    
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of file to detect duplicates"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_bank_info(self, text):
        """Extract bank name and account number from statement"""
        bank_info = {
            'bank_name': None,
            'account_number': None,
            'statement_date': None
        }
        
        # Common bank names
        banks = ['Chase', 'Bank of America', 'Wells Fargo', 'Citibank', 'Capital One', 
                 'US Bank', 'PNC', 'TD Bank', 'HSBC', 'ICICI', 'HDFC', 'SBI', 'Axis']
        
        for bank in banks:
            if bank.lower() in text.lower():
                bank_info['bank_name'] = bank
                break
        
        # Extract account number (last 4 digits pattern)
        account_match = re.search(r'Account\s*(?:Number|No\.?)?\s*[:\-]?\s*[xX*]+(\d{4})', text, re.IGNORECASE)
        if account_match:
            bank_info['account_number'] = f"****{account_match.group(1)}"
        
        # Extract statement date
        date_match = re.search(r'Statement\s+(?:Date|Period)[:\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
        if date_match:
            try:
                date_str = date_match.group(1).strip()
                bank_info['statement_date'] = parser.parse(date_str, fuzzy=True)
            except:
                pass
        
        return bank_info
    
    def extract_transactions(self, text):
        """Extract transactions from statement text"""
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            # Look for lines with dates and amounts
            date_match = None
            for pattern in self.date_patterns:
                date_match = re.search(pattern, line)
                if date_match:
                    break
            
            if not date_match:
                continue
            
            # Find amounts in the line
            amounts = re.findall(self.amount_pattern, line)
            if not amounts:
                continue
            
            # Parse date
            try:
                date_str = date_match.group(0)
                transaction_date = parser.parse(date_str, fuzzy=True)
            except:
                continue
            
            # Extract description (text between date and amount)
            description = line[date_match.end():line.rfind(amounts[-1])].strip()
            
            # Clean description
            description = re.sub(r'\s+', ' ', description)
            description = description[:100]  # Limit length
            
            if not description or len(description) < 3:
                continue
            
            # Parse amount (last amount in line is usually the final amount)
            amount_str = amounts[-1].replace('$', '').replace(',', '').strip()
            
            try:
                amount = float(amount_str)
                
                # Determine transaction type
                transaction_type = 'expense' if amount < 0 or '-' in amounts[-1] else 'income'
                amount = abs(amount)
                
                # Categorize transaction
                category = self.categorize_transaction(description)
                
                transactions.append({
                    'date': transaction_date.isoformat(),
                    'description': description,
                    'amount': amount,
                    'type': transaction_type,
                    'category': category
                })
            except:
                continue
        
        return transactions
    
    def categorize_transaction(self, description):
        """Auto-categorize transaction based on description"""
        description_lower = description.lower()
        
        categories = {
            'Food & Groceries': ['grocery', 'supermarket', 'food', 'restaurant', 'cafe', 'starbucks', 'mcdonald', 'pizza'],
            'Transportation': ['uber', 'lyft', 'gas', 'fuel', 'parking', 'metro', 'bus', 'taxi'],
            'Shopping': ['amazon', 'walmart', 'target', 'mall', 'store', 'shop'],
            'Bills': ['electric', 'water', 'internet', 'phone', 'utility', 'bill', 'payment'],
            'Entertainment': ['netflix', 'spotify', 'movie', 'game', 'entertainment'],
            'Healthcare': ['pharmacy', 'medical', 'doctor', 'hospital', 'health'],
            'Salary': ['salary', 'payroll', 'direct deposit', 'employer']
        }
        
        for category, keywords in categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return 'Other'
    
    def extract_from_pdf(self, pdf_path):
        """Main extraction method"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract text from all pages
                full_text = ""
                for page in pdf.pages:
                    full_text += page.extract_text() + "\n"
                
                # Extract bank info
                bank_info = self.extract_bank_info(full_text)
                
                # Extract transactions
                transactions = self.extract_transactions(full_text)
                
                # Calculate file hash
                file_hash = self.calculate_file_hash(pdf_path)
                
                return {
                    'bank_info': bank_info,
                    'transactions': transactions,
                    'file_hash': file_hash,
                    'success': True
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }