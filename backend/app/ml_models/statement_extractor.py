import pdfplumber
import re
from datetime import datetime
from dateutil import parser
import hashlib

class StatementExtractor:
    def __init__(self):
        # Indian date formats
        self.date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',      # DD/MM/YYYY
            r'\d{1,2}-\d{1,2}-\d{2,4}',      # DD-MM-YYYY
            r'\d{2}\s+[A-Za-z]{3}\s+\d{2,4}', # 15 Jan 2024
            r'\d{1,2}\s+[A-Za-z]+\s+\d{4}',   # 15 January 2024
        ]
        
        # Indian Rupee patterns - handles lakhs and crores format
        self.amount_patterns = [
            r'₹\s*[\d,]+\.?\d*',               # ₹1,23,456.78
            r'Rs\.?\s*[\d,]+\.?\d*',           # Rs 1,23,456.78
            r'INR\s*[\d,]+\.?\d*',             # INR 1,23,456.78
            r'[\d,]+\.?\d*\s*(?:Cr|Dr)',      # 123.45 Cr/Dr
            r'\(\s*[\d,]+\.?\d*\s*\)',        # (123.45) for debits
        ]
        
        # Indian banks
        self.indian_banks = [
            'State Bank of India', 'SBI', 'HDFC', 'ICICI', 'Axis Bank', 
            'Punjab National Bank', 'PNB', 'Bank of Baroda', 'Canara Bank',
            'Union Bank', 'Bank of India', 'Indian Bank', 'Central Bank',
            'IndusInd Bank', 'Yes Bank', 'Kotak Mahindra', 'IDBI', 'UCO Bank'
        ]
        
        # Keywords to identify transaction type
        self.credit_keywords = [
            'credit', 'cr', 'deposit', 'salary', 'credited', 'transfer credit',
            'imps cr', 'neft cr', 'rtgs cr', 'upi cr', 'interest credit'
        ]
        
        self.debit_keywords = [
            'debit', 'dr', 'withdrawal', 'debited', 'payment', 'purchase',
            'imps dr', 'neft dr', 'rtgs dr', 'upi dr', 'pos', 'atm'
        ]
    
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
        
        # Find Indian bank name
        text_lower = text.lower()
        for bank in self.indian_banks:
            if bank.lower() in text_lower:
                bank_info['bank_name'] = bank
                break
        
        # Extract account number (various formats)
        patterns = [
            r'Account\s*(?:Number|No\.?)?\s*[:\-]?\s*[xX*]+(\d{4})',  # ****1234
            r'A/[Cc]\s*(?:No\.?)?\s*[:\-]?\s*[\d\s]+(\d{4})',          # A/C No: 1234
            r'Account\s*[:\-]?\s*(\d{10,16})',                         # Full number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) > 0:
                    bank_info['account_number'] = f"****{match.group(1)}"
                else:
                    # Take last 4 digits
                    full_num = match.group(0)
                    digits = re.findall(r'\d', full_num)
                    if len(digits) >= 4:
                        bank_info['account_number'] = f"****{''.join(digits[-4:])}"
                break
        
        # Extract statement date/period
        date_patterns = [
            r'Statement\s+(?:Period|Date|for)[:\s]+(.+?)(?:\n|to)',
            r'From[:\s]+(.+?)\s+to\s+(.+?)(?:\n|$)',
            r'Statement\s+as\s+on[:\s]+(.+?)(?:\n|$)',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1).strip()
                    # Handle Indian date format (DD/MM/YYYY)
                    bank_info['statement_date'] = parser.parse(date_str, dayfirst=True, fuzzy=True)
                    break
                except:
                    pass
        
        return bank_info
    
    def clean_amount(self, amount_str):
        """Clean and parse Indian number format"""
        # Remove currency symbols and text
        amount_str = re.sub(r'₹|Rs\.?|INR|Cr|Dr', '', amount_str)
        # Remove spaces
        amount_str = amount_str.strip()
        # Check if it's in brackets (debit)
        is_debit = amount_str.startswith('(') and amount_str.endswith(')')
        # Remove brackets
        amount_str = amount_str.replace('(', '').replace(')', '')
        # Remove commas
        amount_str = amount_str.replace(',', '')
        
        try:
            amount = float(amount_str)
            return amount, is_debit
        except:
            return None, False
    
    def determine_transaction_type(self, description, amount_text, is_bracketed):
        """Determine if transaction is credit (income) or debit (expense)"""
        desc_lower = description.lower()
        amount_lower = amount_text.lower()
        
        # Check for explicit Cr/Dr markers
        if 'cr' in amount_lower or any(kw in desc_lower for kw in self.credit_keywords):
            return 'income'
        
        if 'dr' in amount_lower or is_bracketed or any(kw in desc_lower for kw in self.debit_keywords):
            return 'expense'
        
        # If amount has minus sign or in brackets
        if '-' in amount_text or is_bracketed:
            return 'expense'
        
        # Default based on keywords in description
        if any(kw in desc_lower for kw in ['salary', 'deposit', 'credit', 'interest', 'refund']):
            return 'income'
        
        # Default to expense (most transactions are expenses)
        return 'expense'
    
    def extract_transactions(self, text):
        """Extract transactions from Indian bank statement"""
        transactions = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Skip header lines
            if any(header in line.lower() for header in ['date', 'particulars', 'debit', 'credit', 'balance', 'transaction']):
                continue
            
            # Look for date pattern
            date_match = None
            for pattern in self.date_patterns:
                date_match = re.search(pattern, line)
                if date_match:
                    break
            
            if not date_match:
                continue
            
            # Extract date
            try:
                date_str = date_match.group(0)
                transaction_date = parser.parse(date_str, dayfirst=True, fuzzy=True)
            except:
                continue
            
            # Find amounts in current and next few lines
            amount_text = None
            amount_value = None
            description = ""
            is_bracketed = False
            
            # Check current line and next 2 lines for amounts
            check_lines = [line] + lines[i+1:min(i+3, len(lines))]
            combined_text = ' '.join(check_lines)
            
            # Find all amounts
            for pattern in self.amount_patterns:
                amounts = re.findall(pattern, combined_text)
                if amounts:
                    # Take the last amount (usually the transaction amount)
                    amount_text = amounts[-1]
                    amount_value, is_bracketed = self.clean_amount(amount_text)
                    break
            
            if amount_value is None or amount_value == 0:
                continue
            
            # Extract description (text between date and amount, or entire line)
            desc_end = line.rfind(amount_text) if amount_text in line else len(line)
            description = line[date_match.end():desc_end].strip()
            
            # If description is empty, try next line
            if not description and i + 1 < len(lines):
                description = lines[i + 1].strip()
            
            # Clean description
            description = re.sub(r'\s+', ' ', description)
            description = re.sub(r'[^\w\s\-/]', '', description)
            description = description[:150]  # Limit length
            
            if not description or len(description) < 3:
                description = "Transaction"
            
            # Determine transaction type
            transaction_type = self.determine_transaction_type(description, amount_text, is_bracketed)
            
            # Categorize transaction
            category = self.categorize_transaction(description, transaction_type)
            
            transactions.append({
                'date': transaction_date.isoformat(),
                'description': description,
                'amount': amount_value,
                'type': transaction_type,
                'category': category
            })
        
        return transactions
    
    def categorize_transaction(self, description, transaction_type):
        """Auto-categorize transaction based on description"""
        description_lower = description.lower()
        
        # If it's income, categorize as income-related
        if transaction_type == 'income':
            income_categories = {
                'Salary': ['salary', 'payroll', 'employer', 'wage'],
                'Investment': ['dividend', 'interest', 'mutual fund', 'return'],
                'Refund': ['refund', 'cashback', 'reversal'],
                'Transfer': ['transfer', 'neft', 'imps', 'rtgs', 'upi'],
            }
            
            for category, keywords in income_categories.items():
                if any(kw in description_lower for kw in keywords):
                    return category
            return 'Other Income'
        
        # Expense categories
        categories = {
            'Food & Groceries': ['grocery', 'supermarket', 'food', 'swiggy', 'zomato', 'restaurant', 'cafe', 'blinkit', 'bigbasket', 'dmart'],
            'Transportation': ['uber', 'ola', 'rapido', 'petrol', 'fuel', 'parking', 'metro', 'bus', 'taxi', 'fastag'],
            'Shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'meesho', 'mall', 'store', 'shopping'],
            'Bills': ['electricity', 'water', 'gas', 'internet', 'broadband', 'mobile', 'phone', 'recharge', 'utility', 'bill'],
            'Entertainment': ['netflix', 'prime', 'hotstar', 'spotify', 'movie', 'bookmyshow', 'game', 'entertainment'],
            'Healthcare': ['pharmacy', 'medical', 'doctor', 'hospital', 'health', 'clinic', 'apollo', 'medplus'],
            'Insurance': ['insurance', 'premium', 'lic', 'policy'],
            'EMI': ['emi', 'loan', 'repayment'],
            'Investment': ['mutual fund', 'sip', 'stock', 'investment', 'zerodha', 'groww'],
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
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                
                if not full_text:
                    return {
                        'success': False,
                        'error': 'Could not extract text from PDF'
                    }
                
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
                    'success': True,
                    'extracted_text': full_text[:500]  # First 500 chars for debugging
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }