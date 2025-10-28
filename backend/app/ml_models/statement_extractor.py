import pdfplumber
import re
from datetime import datetime
from dateutil import parser
import hashlib

class StatementExtractor:
    def __init__(self):
        # Indian date formats
        self.date_patterns = [
            r'\d{2}-\d{2}-\d{4}',           # DD-MM-YYYY (Karnataka Bank format)
            r'\d{1,2}/\d{1,2}/\d{2,4}',     # DD/MM/YYYY
            r'\d{2}\s+[A-Za-z]{3}\s+\d{2,4}', # 15 Jan 2024
        ]
        
        # Indian banks including regional banks
        self.indian_banks = [
            'State Bank of India', 'SBI', 'HDFC', 'ICICI', 'Axis Bank',
            'Karnataka Bank', 'KBL', 'Canara Bank', 'Punjab National Bank',
            'Bank of Baroda', 'Union Bank', 'Yes Bank', 'Kotak Mahindra',
            'IndusInd Bank', 'Federal Bank', 'South Indian Bank'
        ]
        
        # UPI transaction patterns
        self.upi_pattern = r'UPI:(\d+):([^(]+)\(([^)]+)\)'
        
        # Keywords for transaction type detection
        self.credit_keywords = [
            'credit', 'cr', 'deposit', 'salary', 'credited', 'deposits',
            'refund', 'cashback', 'interest', 'reversal'
        ]
        
        self.debit_keywords = [
            'debit', 'dr', 'withdrawal', 'debited', 'payment', 'withdrawals',
            'purchase', 'atm', 'pos', 'transfer', 'upi'
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
            'statement_date': None,
            'customer_name': None
        }
        
        # Extract customer name
        name_pattern = r'Name\s+(.+?)(?:\n|Address)'
        name_match = re.search(name_pattern, text, re.IGNORECASE)
        if name_match:
            bank_info['customer_name'] = name_match.group(1).strip()
        
        # Find bank name
        text_lower = text.lower()
        for bank in self.indian_banks:
            if bank.lower() in text_lower:
                bank_info['bank_name'] = bank
                break
        
        # If not found, check for specific bank patterns
        if not bank_info['bank_name']:
            if 'kbl' in text_lower or 'karnataka bank' in text_lower:
                bank_info['bank_name'] = 'Karnataka Bank'
        
        # Extract account number (various patterns)
        account_patterns = [
            r'account\s+number\s+(\d+)',
            r'A/c\s+(?:No\.?)?\s*[:\-]?\s*(\d+)',
            r'Account\s*[:\-]?\s*(\d{10,18})',
        ]
        
        for pattern in account_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                full_account = match.group(1)
                # Take last 4 digits
                if len(full_account) >= 4:
                    bank_info['account_number'] = f"****{full_account[-4:]}"
                break
        
        # Extract statement period
        period_pattern = r'Between\s+(\d{2}-\d{2}-\d{4})\s+and\s+(\d{2}-\d{2}-\d{4})'
        period_match = re.search(period_pattern, text)
        if period_match:
            try:
                end_date = parser.parse(period_match.group(2), dayfirst=True)
                bank_info['statement_date'] = end_date
            except:
                pass
        
        return bank_info
    
    def parse_amount(self, amount_str):
        """Parse amount string to float"""
        if not amount_str or amount_str.strip() == '':
            return None
        
        # Remove commas and spaces
        amount_str = amount_str.replace(',', '').strip()
        
        try:
            return float(amount_str)
        except:
            return None
    
    def categorize_upi_transaction(self, description):
        """Categorize UPI transaction based on merchant/description"""
        desc_lower = description.lower()
        
        # UPI transaction categories
        if any(x in desc_lower for x in ['swiggy', 'zomato', 'restaurant', 'food']):
            return 'Food & Groceries'
        
        if any(x in desc_lower for x in ['irctc', 'rail', 'ticket', 'movie', 'district']):
            return 'Transportation'
        
        if any(x in desc_lower for x in ['flipkart', 'amazon', 'shopping', 'store']):
            return 'Shopping'
        
        if any(x in desc_lower for x in ['recharge', 'mobile', 'gpay', 'phonepe']):
            return 'Bills'
        
        if any(x in desc_lower for x in ['medical', 'pharmacy', 'medic', 'rishi']):
            return 'Healthcare'
        
        if any(x in desc_lower for x in ['paytm', 'merchant']):
            return 'Shopping'
        
        # Personal transfers (names)
        if re.search(r'[A-Z]{2,}', description) and 'Payment' not in description:
            return 'Transfer'
        
        return 'Other'
    
    def extract_transactions_table_format(self, text):
        """Extract transactions from Karnataka Bank table format"""
        transactions = []
        lines = text.split('\n')
        
        # Find table data section
        in_table = False
        for i, line in enumerate(lines):
            # Skip headers and account info
            if 'Date' in line and 'Particulars' in line and 'Balance' in line:
                in_table = True
                continue
            
            if not in_table:
                continue
            
            # Stop at closing balance or end markers
            if 'Closing Balance' in line or 'system generated' in line.lower():
                break
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Parse line with date pattern
            date_match = re.search(r'(\d{2}-\d{2}-\d{4})', line)
            if not date_match:
                continue
            
            try:
                transaction_date = parser.parse(date_match.group(1), dayfirst=True)
            except:
                continue
            
            # Extract the rest of the line after date
            rest_of_line = line[date_match.end():].strip()
            
            # Split by whitespace to get components
            parts = rest_of_line.split()
            
            if len(parts) < 3:
                continue
            
            # Extract description and amounts
            # Format: Date Description Withdrawal Deposit Balance
            # Last 3 parts are usually: withdrawal, deposit, balance
            
            balance = None
            withdrawal = None
            deposit = None
            
            # Try to find amounts (they have commas or decimals)
            amount_candidates = []
            description_parts = []
            
            for part in parts:
                # Check if it's a number (with commas and decimals)
                if re.match(r'[\d,]+\.?\d*$', part):
                    amount_candidates.append(part)
                else:
                    description_parts.append(part)
            
            # Need at least 1 amount (balance)
            if len(amount_candidates) < 1:
                continue
            
            # Get balance (always last)
            balance = self.parse_amount(amount_candidates[-1])
            
            # Get withdrawal and deposit
            if len(amount_candidates) == 3:
                withdrawal = self.parse_amount(amount_candidates[0])
                deposit = self.parse_amount(amount_candidates[1])
            elif len(amount_candidates) == 2:
                # One of withdrawal or deposit
                first_amount = self.parse_amount(amount_candidates[0])
                if first_amount:
                    # Determine if it's withdrawal or deposit based on description
                    desc_text = ' '.join(description_parts).lower()
                    if any(kw in desc_text for kw in self.credit_keywords):
                        deposit = first_amount
                    else:
                        withdrawal = first_amount
            
            # Join description
            description = ' '.join(description_parts)
            
            # Clean description
            description = re.sub(r'\s+', ' ', description).strip()
            
            if not description or len(description) < 3:
                continue
            
            # Determine transaction type
            if withdrawal and withdrawal > 0:
                amount = withdrawal
                txn_type = 'expense'
            elif deposit and deposit > 0:
                amount = deposit
                txn_type = 'income'
            else:
                continue
            
            # Categorize
            category = self.categorize_upi_transaction(description)
            
            # Clean description (remove UPI IDs)
            description = re.sub(r'UPI:\d+:', '', description)
            description = re.sub(r'@[a-z]+', '', description)
            description = description.strip()
            
            if len(description) > 100:
                description = description[:100]
            
            transactions.append({
                'date': transaction_date.isoformat(),
                'description': description,
                'amount': amount,
                'type': txn_type,
                'category': category
            })
        
        return transactions
    
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
                
                print("="*60)
                print("EXTRACTED TEXT PREVIEW:")
                print(full_text[:500])
                print("="*60)
                
                # Extract bank info
                bank_info = self.extract_bank_info(full_text)
                print(f"Bank Info: {bank_info}")
                
                # Extract transactions
                transactions = self.extract_transactions_table_format(full_text)
                print(f"Transactions found: {len(transactions)}")
                
                if transactions:
                    print("Sample transactions:")
                    for txn in transactions[:3]:
                        print(f"  {txn['date']}: {txn['description']} - ₹{txn['amount']} ({txn['type']})")
                
                # Calculate file hash
                file_hash = self.calculate_file_hash(pdf_path)
                
                return {
                    'bank_info': bank_info,
                    'transactions': transactions,
                    'file_hash': file_hash,
                    'success': True,
                    'extracted_text_preview': full_text[:1000]
                }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }