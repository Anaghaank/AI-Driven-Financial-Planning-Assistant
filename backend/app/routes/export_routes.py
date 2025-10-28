from flask import Blueprint, send_file, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
import pandas as pd
from io import BytesIO
from datetime import datetime

bp = Blueprint('export', __name__)

@bp.route('/transactions/csv', methods=['GET'])
@jwt_required()
def export_csv():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user, limit=10000)
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Format for export
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%d-%m-%Y')
        df = df[['date', 'description', 'category', 'type', 'amount']]
        df.columns = ['Date', 'Description', 'Category', 'Type', 'Amount (₹)']
        
        # Create CSV in memory
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        filename = f"transactions_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/transactions/excel', methods=['GET'])
@jwt_required()
def export_excel():
    try:
        current_user = get_jwt_identity()
        transactions = Transaction.find_by_user(current_user, limit=10000)
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Format for export
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%d-%m-%Y')
        df = df[['date', 'description', 'category', 'type', 'amount']]
        df.columns = ['Date', 'Description', 'Category', 'Type', 'Amount (₹)']
        
        # Create Excel in memory with styling
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Transactions')
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Transactions']
            
            # Style header
            from openpyxl.styles import Font, PatternFill, Alignment
            
            header_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
        
        output.seek(0)
        
        filename = f"transactions_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500