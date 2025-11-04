import pdfplumber
import re
from datetime import datetime
from dateutil import parser
import hashlib
import pandas as pd

class StatementExtractor:
    def __init__(self):
        # Indian date formats
        self.date_patterns = [
            r'\d{2}-\d{2}-\d{4}',           # DD-MM-YYYY (Karnataka Bank format)
            r'\d{1,2}/\d{1,2}/\d{2,4}',     # DD/MM/YYYY
            r'\d{2}\s+[A-Za-z]{3}\s+\d{2,4}', # 15 Jan 2024
            r'\d{4}-\d{2}-\d{2}',           # YYYY-MM-DD
        ]
        
        # Indian banks including regional banks
        self.indian_banks = [
            'State Bank of India', 'SBI', 'HDFC', 'ICICI', 'Axis Bank',
            'Karnataka Bank', 'KBL', 'Canara Bank', 'Punjab National Bank',
            'Bank of Baroda', 'Union Bank', 'Yes Bank', 'Kotak Mahindra',
            'IndusInd Bank', 'Federal Bank', 'South Indian Bank'
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
            'customer_name': None,
            'opening_balance': None,
            'closing_balance': None
        }
        
        # Extract customer name
        name_patterns = [
            r'Name\s+(.+?)(?:\n)',
            r'Customer\s+Name\s*[:\-]?\s*(.+?)(?:\n)',
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, text, re.IGNORECASE)
            if name_match:
                bank_info['customer_name'] = name_match.group(1).strip()
                break
        
        # Find bank name
        text_lower = text.lower()
        for bank in self.indian_banks:
            if bank.lower() in text_lower:
                bank_info['bank_name'] = bank
                break
        
        # Karnataka Bank specific
        if 'kbl' in text_lower or 'karnataka bank' in text_lower:
            bank_info['bank_name'] = 'Karnataka Bank'
        
        # Extract account number
        account_patterns = [
            r'account\s+number\s+(\d+)',
            r'Statement\s+for\s+account\s+number\s+(\d+)',
            r'A/c\s+(?:No\.?)?\s*[:\-]?\s*(\d+)',
        ]
        
        for pattern in account_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                full_account = match.group(1)
                bank_info['full_account_number'] = full_account
                if len(full_account) >= 4:
                    bank_info['account_number'] = f"****{full_account[-4:]}"
                break
        
        # Extract opening balance
        opening_match = re.search(r'Opening\s+Balance\s+([\d,]+\.?\d*)', text, re.IGNORECASE)
        if opening_match:
            bank_info['opening_balance'] = self.parse_amount(opening_match.group(1))
        
        # Extract closing balance
        closing_match = re.search(r'Closing\s+Balance\s+([\d,]+\.?\d*)', text, re.IGNORECASE)
        if closing_match:
            bank_info['closing_balance'] = self.parse_amount(closing_match.group(1))
        
        # Extract statement period
        period_match = re.search(r'Between\s+(\d{2}-\d{2}-\d{4})\s+and\s+(\d{2}-\d{2}-\d{4})', text, re.IGNORECASE)
        if period_match:
            try:
                start_date = parser.parse(period_match.group(1), dayfirst=True)
                end_date = parser.parse(period_match.group(2), dayfirst=True)
                bank_info['statement_period'] = {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
                bank_info['statement_date'] = end_date
            except:
                pass
        
        return bank_info
    
    def parse_amount(self, amount_str):
        """Parse amount string to float - handles Indian number format"""
        if not amount_str or str(amount_str).strip() in ['', 'None', 'nan']:
            return None
        
        # Convert to string and clean
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and spaces
        amount_str = re.sub(r'[₹Rs\s]', '', amount_str)
        
        # Remove commas (Indian thousands separator)
        amount_str = amount_str.replace(',', '')
        
        # Handle empty after cleaning
        if not amount_str:
            return None
        
        try:
            return float(amount_str)
        except:
            return None
    
    def categorize_transaction(self, description):
        """Enhanced categorization for transactions"""
        desc_lower = description.lower()
        
        # Food & Dining
        if any(x in desc_lower for x in ['swiggy', 'zomato', 'restaurant', 'food', 'cafe', 
                                          'dominos', 'pizza', 'mcdonald', 'kfc', 'subway']):
            return 'Food & Dining'
        
        # Transportation
        if any(x in desc_lower for x in ['irctc', 'rail', 'uber', 'ola', 'rapido', 'fuel',
                                          'petrol', 'diesel', 'fastag', 'parking', 'ticket']):
            return 'Transportation'
        
        # Shopping
        if any(x in desc_lower for x in ['flipkart', 'amazon', 'shopping', 'store', 'myntra',
                                          'ajio', 'meesho', 'mart', 'supermarket', 'paytm', 
                                          'phonepe', 'merchant', 'gpay', 'bharatpe']):
            return 'Shopping'
        
        # Bills & Utilities
        if any(x in desc_lower for x in ['recharge', 'mobile', 'electricity', 'water', 'gas',
                                          'internet', 'broadband', 'dth', 'jio', 'airtel', 'vodafone']):
            return 'Bills & Utilities'
        
        # Healthcare
        if any(x in desc_lower for x in ['medical', 'pharmacy', 'medic', 'hospital', 'clinic',
                                          'doctor', 'apollo', 'fortis', '1mg', 'rishi']):
            return 'Healthcare'
        
        # Entertainment
        if any(x in desc_lower for x in ['movie', 'cinema', 'netflix', 'prime', 'hotstar',
                                          'spotify', 'youtube', 'gaming', 'entertainment', 'district']):
            return 'Entertainment'
        
        # ATM Withdrawal
        if any(x in desc_lower for x in ['atm', 'cash withdrawal', 'cwt']):
            return 'ATM Withdrawal'
        
        # Check if it looks like a personal transfer (has names in caps)
        if re.search(r'[A-Z]{2,}', description) and 'merchant' not in desc_lower:
            return 'Transfer'
        
        return 'Other'
    
    def extract_transactions_from_table(self, pdf):
        """Extract transactions using pdfplumber's table detection"""
        transactions = []
        
        print("\n🔍 Attempting table extraction...")
        
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"\n   📄 Processing page {page_num}...")
            
            # Try multiple extraction strategies
            strategies = [
                {
                    'vertical_strategy': "text",
                    'horizontal_strategy': "text",
                    'snap_tolerance': 3,
                    'join_tolerance': 3,
                },
                {
                    'vertical_strategy': "lines",
                    'horizontal_strategy': "lines",
                    'snap_tolerance': 5,
                },
                {
                    'vertical_strategy': "explicit",
                    'horizontal_strategy': "explicit",
                    'explicit_vertical_lines': [],
                    'explicit_horizontal_lines': [],
                }
            ]
            
            page_transactions = []
            
            for strategy_num, strategy in enumerate(strategies, 1):
                try:
                    tables = page.extract_tables(strategy)
                    
                    if not tables:
                        continue
                    
                    print(f"      Strategy {strategy_num}: Found {len(tables)} table(s)")
                    
                    for table_num, table in enumerate(tables, 1):
                        if not table or len(table) < 2:
                            continue
                        
                        print(f"      Table {table_num}: {len(table)} rows")
                        
                        # Find header row
                        header_row_idx = None
                        for idx, row in enumerate(table[:5]):
                            if row:
                                row_text = ' '.join([str(cell).lower() if cell else '' for cell in row])
                                if 'date' in row_text and ('particular' in row_text or 'withdrawal' in row_text):
                                    header_row_idx = idx
                                    break
                        
                        if header_row_idx is None:
                            # Try without header - assume first row is data
                            header_row_idx = -1
                            headers = ['Date', 'Particulars', 'Withdrawals', 'Deposits', 'Balance']
                        else:
                            headers = table[header_row_idx]
                        
                        # Identify columns
                        date_col = None
                        desc_col = None
                        withdrawal_col = None
                        deposit_col = None
                        balance_col = None
                        
                        for i, header in enumerate(headers):
                            if not header:
                                continue
                            h = str(header).lower()
                            if 'date' in h:
                                date_col = i
                            elif 'particular' in h or 'description' in h:
                                desc_col = i
                            elif 'withdrawal' in h or 'debit' in h:
                                withdrawal_col = i
                            elif 'deposit' in h or 'credit' in h:
                                deposit_col = i
                            elif 'balance' in h:
                                balance_col = i
                        
                        # If no columns identified, try positional (common Karnataka Bank format)
                        if date_col is None:
                            date_col = 0
                            desc_col = 1
                            withdrawal_col = 2
                            deposit_col = 3
                            balance_col = 4
                        
                        # Process data rows
                        rows_processed = 0
                        for row_idx, row in enumerate(table[header_row_idx + 1:], 1):
                            if not row or len(row) < 2:
                                continue
                            
                            # Skip rows that look like headers or footers
                            row_text = ' '.join([str(cell) for cell in row if cell]).lower()
                            if 'closing balance' in row_text or 'opening balance' in row_text:
                                continue
                            if 'date' in row_text and 'particular' in row_text:
                                continue
                            
                            try:
                                # Extract date
                                date_str = None
                                if date_col is not None and date_col < len(row):
                                    date_str = str(row[date_col]).strip() if row[date_col] else None
                                
                                if not date_str or date_str == 'None':
                                    continue
                                
                                # Must start with date pattern
                                if not re.match(r'\d{2}-\d{2}-\d{4}', date_str):
                                    continue
                                
                                # Parse date
                                transaction_date = None
                                try:
                                    transaction_date = parser.parse(date_str, dayfirst=True)
                                except:
                                    continue
                                
                                # Extract description
                                description = ''
                                if desc_col is not None and desc_col < len(row):
                                    description = str(row[desc_col]).strip() if row[desc_col] else ''
                                
                                if not description or description == 'None' or len(description) < 3:
                                    continue
                                
                                # Extract amounts
                                withdrawal = None
                                deposit = None
                                balance = None
                                
                                if withdrawal_col is not None and withdrawal_col < len(row):
                                    withdrawal = self.parse_amount(row[withdrawal_col])
                                
                                if deposit_col is not None and deposit_col < len(row):
                                    deposit = self.parse_amount(row[deposit_col])
                                
                                if balance_col is not None and balance_col < len(row):
                                    balance = self.parse_amount(row[balance_col])
                                
                                # Determine transaction type and amount
                                if withdrawal and withdrawal > 0:
                                    amount = withdrawal
                                    txn_type = 'expense'
                                elif deposit and deposit > 0:
                                    amount = deposit
                                    txn_type = 'income'
                                else:
                                    continue
                                
                                # Clean description
                                description = re.sub(r'UPI:\d+:', '', description)
                                description = re.sub(r'@[a-z]+', '', description)
                                description = re.sub(r'\s+', ' ', description).strip()
                                
                                if len(description) > 100:
                                    description = description[:97] + "..."
                                
                                # Categorize
                                category = self.categorize_transaction(description)
                                
                                transaction = {
                                    'date': transaction_date.isoformat(),
                                    'description': description,
                                    'amount': amount,
                                    'type': txn_type,
                                    'category': category,
                                    'balance': balance
                                }
                                
                                page_transactions.append(transaction)
                                rows_processed += 1
                                
                            except Exception as e:
                                continue
                        
                        if rows_processed > 0:
                            print(f"         ✅ Extracted {rows_processed} transactions")
                    
                    # If we got transactions, no need to try other strategies
                    if page_transactions:
                        break
                        
                except Exception as e:
                    print(f"      ⚠️  Strategy {strategy_num} failed: {e}")
                    continue
            
            transactions.extend(page_transactions)
        
        print(f"\n   📊 Total from table extraction: {len(transactions)} transactions")
        return transactions
    
    def extract_transactions_from_text(self, text):
        """Fallback: Extract transactions from raw text using advanced regex"""
        transactions = []
        
        print("\n🔍 Using text-based extraction (fallback)...")
        
        lines = text.split('\n')
        in_table = False
        transaction_count = 0
        
        for line_num, line in enumerate(lines, 1):
            # Check if we're entering a transaction section (handle multiple table headers)
            if 'Date' in line and 'Particulars' in line and ('Withdrawal' in line or 'Balance' in line):
                in_table = True
                print(f"   Found transaction table header at line {line_num}")
                continue
            
            # Skip opening balance line
            if 'Opening Balance' in line:
                continue
            
            if not in_table:
                continue
            
            # Stop only at the final system generated statement line
            if 'This is a system generated' in line.lower():
                print(f"   Reached end of statement at line {line_num}")
                break
            
            # Don't stop at "Closing Balance" - it might appear multiple times
            if 'Closing Balance' in line and 'system' not in lines[min(line_num, len(lines)-1)].lower():
                continue
            
            if not line.strip():
                continue
            
            # Look for date pattern at start of line
            date_match = re.match(r'(\d{2}-\d{2}-\d{4})\s+(.+)', line)
            if not date_match:
                continue
            
            try:
                transaction_date = parser.parse(date_match.group(1), dayfirst=True)
                rest = date_match.group(2).strip()
                
                # Extract all numbers from the line (including decimals)
                # Pattern matches: 1,500.00 or 206.17 or 834.12
                numbers = re.findall(r'(\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2})', rest)
                
                if len(numbers) < 1:
                    continue
                
                # Parse numbers
                parsed_numbers = [self.parse_amount(n) for n in numbers]
                parsed_numbers = [n for n in parsed_numbers if n is not None and n > 0]
                
                if len(parsed_numbers) < 1:
                    continue
                
                # Determine which numbers are what:
                # Karnataka Bank format: Description Amount Balance
                # OR: Description Withdrawal Deposit Balance
                
                balance = parsed_numbers[-1]  # Last number is always balance
                
                if len(parsed_numbers) == 1:
                    # Only balance, skip this line
                    continue
                elif len(parsed_numbers) == 2:
                    # Description Amount Balance (single transaction)
                    amount = parsed_numbers[0]
                elif len(parsed_numbers) >= 3:
                    # Description Withdrawal Deposit Balance
                    # Take second-to-last as the transaction amount
                    amount = parsed_numbers[-2]
                else:
                    continue
                
                # Extract description (everything before the first number)
                first_num_pos = rest.find(numbers[0])
                description = rest[:first_num_pos].strip()
                
                if len(description) < 3:
                    continue
                
                # Clean description
                description_clean = re.sub(r'UPI:\d+:', '', description)
                description_clean = re.sub(r'@[a-z]+', '', description_clean)
                description_clean = re.sub(r'\s+', ' ', description_clean).strip()
                
                if len(description_clean) > 100:
                    description_clean = description_clean[:97] + "..."
                
                # Determine type by checking if it's a deposit/credit
                # Most UPI transactions from others are deposits (income)
                # Check the original transaction for patterns
                is_deposit = False
                desc_lower = description.lower()
                
                # Keywords that indicate money coming IN (deposits/income)
                deposit_keywords = ['credit', 'deposit', 'salary', 'refund', 'reversal', 'received']
                
                # If description contains someone's name sending money, it's income
                # UPI format: sendername@provider means someone sent you money
                if 'upi:' in desc_lower:
                    # This is a UPI transaction - need to determine direction
                    # If it shows payment TO someone/merchant, it's expense
                    # If it's FROM someone, it's income
                    if any(kw in desc_lower for kw in ['payment', 'merchant', 'paytm', 'phonepe', 'gpay']):
                        is_deposit = False  # Payment made
                    else:
                        # Check if previous balance > current balance (expense)
                        # This is more reliable
                        is_deposit = False  # Default to expense for UPI
                
                if any(kw in desc_lower for kw in deposit_keywords):
                    is_deposit = True
                
                txn_type = 'income' if is_deposit else 'expense'
                
                # Categorize
                category = self.categorize_transaction(description_clean)
                
                transaction = {
                    'date': transaction_date.isoformat(),
                    'description': description_clean,
                    'amount': amount,
                    'type': txn_type,
                    'category': category,
                    'balance': balance
                }
                
                transactions.append(transaction)
                transaction_count += 1
                
            except Exception as e:
                continue
        
        print(f"   ✅ Extracted {transaction_count} transactions from text")
        return transactions
    
    def extract_from_pdf(self, pdf_path):
        """Main extraction method with dual strategy"""
        try:
            print(f"\n{'='*80}")
            print(f"📄 EXTRACTING FROM: {pdf_path}")
            print(f"{'='*80}")
            
            with pdfplumber.open(pdf_path) as pdf:
                # Extract full text
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
                
                print("\n📋 Extracted text preview (first 500 chars):")
                print("-" * 80)
                print(full_text[:500])
                print("-" * 80)
                
                # Extract bank info
                bank_info = self.extract_bank_info(full_text)
                print(f"\n🏦 Bank Info:")
                print(f"   Bank: {bank_info.get('bank_name')}")
                print(f"   Account: {bank_info.get('account_number')}")
                print(f"   Customer: {bank_info.get('customer_name')}")
                print(f"   Opening Balance: ₹{bank_info.get('opening_balance', 0):,.2f}")
                print(f"   Closing Balance: ₹{bank_info.get('closing_balance', 0):,.2f}")
                
                # Try table extraction first
                transactions = self.extract_transactions_from_table(pdf)
                print(f"\n✅ Table extraction found: {len(transactions)} transactions")
                
                # Always try text parsing as well and compare
                text_transactions = self.extract_transactions_from_text(full_text)
                print(f"✅ Text extraction found: {len(text_transactions)} transactions")
                
                # Use whichever method found more transactions
                if len(text_transactions) > len(transactions):
                    print(f"   📝 Using text extraction results (more complete)")
                    transactions = text_transactions
                else:
                    print(f"   📊 Using table extraction results")
                
                # Remove duplicates based on date, amount, and description
                unique_transactions = []
                seen = set()
                
                for txn in transactions:
                    key = (txn['date'], txn['amount'], txn['description'][:30])
                    if key not in seen:
                        seen.add(key)
                        unique_transactions.append(txn)
                
                transactions = unique_transactions
                
                print(f"\n📊 Final count: {len(transactions)} transactions")
                
                if transactions:
                    print("\n📝 Sample transactions (first 3):")
                    for i, txn in enumerate(transactions[:3], 1):
                        print(f"   {i}. {txn['date'][:10]}: {txn['description'][:50]}")
                        print(f"      Amount: ₹{txn['amount']:,.2f} | Type: {txn['type']} | Category: {txn['category']}")
                
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
            print("\n❌ ERROR during extraction:")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }