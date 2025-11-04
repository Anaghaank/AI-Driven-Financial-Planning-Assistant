"""
Simple test script for bank statement extraction
Run this to test your PDF extraction
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ml_models.statement_extractor import StatementExtractor

def test_extraction(pdf_path):
    """Test extraction on a PDF file"""
    
    print("=" * 80)
    print("TESTING BANK STATEMENT EXTRACTION")
    print("=" * 80)
    print(f"\nFile: {pdf_path}")
    print(f"File exists: {os.path.exists(pdf_path)}")
    print()
    
    if not os.path.exists(pdf_path):
        print("❌ ERROR: File not found!")
        print(f"   Looking in: {os.path.abspath(pdf_path)}")
        return
    
    # Initialize extractor
    print("📄 Initializing extractor...")
    extractor = StatementExtractor()
    
    print("📄 Extracting data from PDF...\n")
    result = extractor.extract_from_pdf(pdf_path)
    
    if not result['success']:
        print(f"\n❌ EXTRACTION FAILED")
        print(f"Error: {result.get('error')}")
        return
    
    print("\n✅ EXTRACTION SUCCESSFUL\n")
    
    # Print bank information
    bank_info = result.get('bank_info', {})
    print("=" * 80)
    print("BANK INFORMATION")
    print("=" * 80)
    print(f"Bank Name:          {bank_info.get('bank_name', 'N/A')}")
    print(f"Account Number:     {bank_info.get('account_number', 'N/A')}")
    print(f"Customer Name:      {bank_info.get('customer_name', 'N/A')}")
    print(f"Opening Balance:    ₹{bank_info.get('opening_balance', 0):,.2f}")
    print(f"Closing Balance:    ₹{bank_info.get('closing_balance', 0):,.2f}")
    
    if bank_info.get('statement_period'):
        period = bank_info['statement_period']
        print(f"Statement Period:   {period.get('start', 'N/A')} to {period.get('end', 'N/A')}")
    
    # Print transactions
    transactions = result.get('transactions', [])
    print(f"\nTotal Transactions: {len(transactions)}")
    
    if transactions:
        print("\n" + "=" * 80)
        print("SAMPLE TRANSACTIONS (First 10)")
        print("=" * 80)
        
        for i, txn in enumerate(transactions[:10], 1):
            date = txn.get('date', 'N/A')
            if isinstance(date, str):
                date = date[:10]  # Show only date part
            
            print(f"\n{i}. {date}")
            print(f"   Description: {txn.get('description', 'N/A')[:70]}")
            print(f"   Amount:      ₹{txn.get('amount', 0):,.2f}")
            print(f"   Type:        {txn.get('type', 'N/A').upper()}")
            print(f"   Category:    {txn.get('category', 'N/A')}")
        
        # Category summary
        print("\n" + "=" * 80)
        print("CATEGORY BREAKDOWN")
        print("=" * 80)
        
        category_totals = {}
        for txn in transactions:
            category = txn.get('category', 'Other')
            amount = txn.get('amount', 0)
            txn_type = txn.get('type', 'expense')
            
            if category not in category_totals:
                category_totals[category] = {
                    'debit': 0,
                    'credit': 0,
                    'count': 0
                }
            
            if txn_type == 'expense':
                category_totals[category]['debit'] += amount
            else:
                category_totals[category]['credit'] += amount
            
            category_totals[category]['count'] += 1
        
        # Sort by total amount (debit + credit)
        sorted_categories = sorted(
            category_totals.items(),
            key=lambda x: x[1]['debit'] + x[1]['credit'],
            reverse=True
        )
        
        for category, totals in sorted_categories:
            print(f"\n📊 {category}")
            print(f"   Transactions: {totals['count']}")
            if totals['debit'] > 0:
                print(f"   Expenses:     ₹{totals['debit']:,.2f}")
            if totals['credit'] > 0:
                print(f"   Income:       ₹{totals['credit']:,.2f}")
        
        # Type summary
        print("\n" + "=" * 80)
        print("TRANSACTION TYPE SUMMARY")
        print("=" * 80)
        
        total_expense = sum(txn.get('amount', 0) for txn in transactions if txn.get('type') == 'expense')
        total_income = sum(txn.get('amount', 0) for txn in transactions if txn.get('type') == 'income')
        expense_count = sum(1 for txn in transactions if txn.get('type') == 'expense')
        income_count = sum(1 for txn in transactions if txn.get('type') == 'income')
        
        print(f"\n💸 Total Expenses:  ₹{total_expense:,.2f} ({expense_count} transactions)")
        print(f"💰 Total Income:    ₹{total_income:,.2f} ({income_count} transactions)")
        print(f"📈 Net Change:      ₹{(total_income - total_expense):,.2f}")
        
        # Verify against bank info
        if bank_info.get('opening_balance') and bank_info.get('closing_balance'):
            expected_change = bank_info['closing_balance'] - bank_info['opening_balance']
            actual_change = total_income - total_expense
            print(f"\n🔍 Verification:")
            print(f"   Expected Change: ₹{expected_change:,.2f}")
            print(f"   Actual Change:   ₹{actual_change:,.2f}")
            if abs(expected_change - actual_change) < 1:
                print(f"   ✅ Balanced!")
            else:
                print(f"   ⚠️  Difference:    ₹{abs(expected_change - actual_change):,.2f}")
    else:
        print("\n⚠️  No transactions found in the statement")
        print("\nPossible reasons:")
        print("  - PDF might be image-based (scanned) rather than text-based")
        print("  - PDF format is not recognized")
        print("  - Text extraction failed")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    # Default test file
    test_file = "test_bank_statement_sbi.pdf"
    
    # Check if file path provided as argument
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    # Check common locations
    possible_paths = [
        test_file,
        os.path.join("uploads", test_file),
        os.path.join("..", test_file),
    ]
    
    pdf_path = None
    for path in possible_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        print(f"❌ Could not find file: {test_file}")
        print(f"\nSearched in:")
        for path in possible_paths:
            print(f"  - {os.path.abspath(path)}")
        print(f"\n💡 Usage: python test_extraction.py <path_to_pdf>")
        sys.exit(1)
    
    test_extraction(pdf_path)