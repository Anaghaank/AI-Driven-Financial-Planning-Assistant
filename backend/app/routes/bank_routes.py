from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.bank import Bank
from app.models.statement_upload import StatementUpload
from app.models.transaction import Transaction
from app.ml_models.statement_extractor import StatementExtractor
import os
from werkzeug.utils import secure_filename

bp = Blueprint('banks', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('', methods=['GET'])
@jwt_required()
def get_banks():
    try:
        current_user = get_jwt_identity()
        banks = Bank.find_by_user(current_user)
        return jsonify(banks), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('', methods=['POST'])
@jwt_required()
def create_bank():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        bank = Bank.create(current_user, data)
        return jsonify(bank), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/upload-statement', methods=['POST'])
@jwt_required()
def upload_statement():
    try:
        current_user = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, f"{current_user}_{filename}")
        file.save(filepath)
        
        print(f"📁 Saved file to: {filepath}")
        
        # Extract data from PDF
        extractor = StatementExtractor()
        result = extractor.extract_from_pdf(filepath)
        
        if not result['success']:
            os.remove(filepath)
            return jsonify({'error': result['error']}), 400
        
        # Check for duplicate upload
        existing = StatementUpload.find_by_hash(current_user, result['file_hash'])
        if existing:
            os.remove(filepath)
            return jsonify({
                'message': 'This statement has already been uploaded',
                'duplicate': True,
                'uploaded_at': existing['uploaded_at']
            }), 200
        
        bank_info = result['bank_info']
        transactions = result['transactions']
        
        print(f"✅ Extracted {len(transactions)} transactions")
        print(f"🏦 Bank: {bank_info.get('bank_name')}")
        print(f"💰 Opening Balance: {bank_info.get('opening_balance')}")
        print(f"💰 Closing Balance: {bank_info.get('closing_balance')}")
        
        # Find or create bank account
        bank = None
        account_to_match = bank_info.get('full_account_number') or bank_info.get('account_number')
        
        if account_to_match:
            bank = Bank.find_by_account(current_user, account_to_match)
        
        if not bank and bank_info['bank_name']:
            # Create new bank account
            bank = Bank.create(current_user, {
                'bank_name': bank_info['bank_name'],
                'account_number': bank_info.get('account_number', 'Unknown'),
                'account_type': 'Savings',
                'balance': bank_info.get('closing_balance', 0),
                'is_active': True
            })
            print(f"✨ Created new bank account: {bank.get('_id')}")
        elif bank:
            # Update existing bank balance
            Bank.update_balance(str(bank['_id']), bank_info.get('closing_balance', bank.get('balance', 0)))
            print(f"🔄 Updated bank balance")
        
        # Add transactions
        added_count = 0
        skipped_count = 0
        
        for txn in transactions:
            try:
                # Check if transaction already exists to avoid duplicates
                existing_txn = Transaction.find_duplicate(
                    current_user,
                    txn['date'],
                    txn['amount'],
                    txn['description'][:50]
                )
                
                if existing_txn:
                    skipped_count += 1
                    continue
                
                Transaction.create(current_user, txn)
                added_count += 1
            except Exception as e:
                print(f"⚠️ Error adding transaction: {e}")
                skipped_count += 1
        
        print(f"✅ Added {added_count} new transactions")
        print(f"⏭️ Skipped {skipped_count} duplicate transactions")
        
        # Record statement upload
        StatementUpload.create(current_user, {
            'bank_id': str(bank['_id']) if bank else None,
            'filename': filename,
            'file_hash': result['file_hash'],
            'statement_date': bank_info.get('statement_date'),
            'transactions_count': added_count
        })
        
        # Clean up file
        os.remove(filepath)
        
        return jsonify({
            'message': 'Statement processed successfully',
            'bank_info': {
                'bank_name': bank_info.get('bank_name'),
                'account_number': bank_info.get('account_number'),
                'customer_name': bank_info.get('customer_name'),
                'opening_balance': bank_info.get('opening_balance'),
                'closing_balance': bank_info.get('closing_balance'),
            },
            'transactions_added': added_count,
            'transactions_skipped': skipped_count,
            'total_extracted': len(transactions),
            'duplicate': False
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@bp.route('/statements', methods=['GET'])
@jwt_required()
def get_statements():
    try:
        current_user = get_jwt_identity()
        statements = StatementUpload.find_by_user(current_user)
        return jsonify(statements), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500