from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def create_indian_bank_statement():
    """Create a sample Indian bank statement PDF for testing"""
    
    filename = "test_bank_statement_sbi.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Bank name and header
    title = Paragraph("STATE BANK OF INDIA", title_style)
    story.append(title)
    
    subtitle = Paragraph("Account Statement", styles['Heading2'])
    story.append(subtitle)
    story.append(Spacer(1, 0.3*inch))
    
    # Account details
    account_data = [
        ['Account Number:', 'XXXX XXXX 1234'],
        ['Account Holder:', 'Test User'],
        ['Account Type:', 'Savings Account'],
        ['Statement Period:', '01/01/2024 to 31/01/2024'],
        ['Branch:', 'Delhi Main Branch'],
    ]
    
    account_table = Table(account_data, colWidths=[2*inch, 3*inch])
    account_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(account_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Transaction table header
    transaction_header = Paragraph("<b>Transaction Details</b>", styles['Heading3'])
    story.append(transaction_header)
    story.append(Spacer(1, 0.2*inch))
    
    # Transaction data
    transaction_data = [
        ['Date', 'Particulars', 'Debit (₹)', 'Credit (₹)', 'Balance (₹)'],
        ['01/01/2024', 'Opening Balance', '', '', '50,000.00'],
        ['05/01/2024', 'Salary Credit - ABC Corporation', '', '75,000.00', '1,25,000.00'],
        ['08/01/2024', 'UPI-Swiggy Food Order', '450.00', '', '1,24,550.00'],
        ['10/01/2024', 'NEFT Transfer - Rent Payment', '25,000.00', '', '99,550.00'],
        ['12/01/2024', 'UPI-Amazon Shopping', '3,500.00', '', '96,050.00'],
        ['15/01/2024', 'Electricity Bill Payment', '2,100.00', '', '93,950.00'],
        ['18/01/2024', 'ATM Withdrawal - SBI ATM', '5,000.00', '', '88,950.00'],
        ['20/01/2024', 'UPI-Zomato Food Delivery', '650.00', '', '88,300.00'],
        ['22/01/2024', 'Mobile Recharge - Jio', '599.00', '', '87,701.00'],
        ['25/01/2024', 'UPI-BigBasket Groceries', '4,200.00', '', '83,501.00'],
        ['28/01/2024', 'Interest Credit', '', '125.50', '83,626.50'],
        ['30/01/2024', 'UPI-Uber Ride', '180.00', '', '83,446.50'],
        ['31/01/2024', 'Closing Balance', '', '', '83,446.50'],
    ]
    
    # Create transaction table
    transaction_table = Table(transaction_data, colWidths=[1*inch, 2.5*inch, 1*inch, 1*inch, 1.2*inch])
    transaction_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (2, 1), (4, -1), 'RIGHT'),  # Right align numbers
        ('ALIGN', (0, 1), (1, -1), 'LEFT'),   # Left align text
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Alternate row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        
        # Highlight opening and closing balance
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e6f2ff')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e6f2ff')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(transaction_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    summary_data = [
        ['Total Credits:', '₹ 75,125.50'],
        ['Total Debits:', '₹ 41,679.00'],
        ['Net Change:', '₹ 33,446.50'],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer = Paragraph("<i>This is a computer-generated statement and does not require signature.</i>", styles['Normal'])
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    print(f"✅ Test bank statement created: {filename}")
    return filename

if __name__ == '__main__':
    # Install reportlab if not already installed
    try:
        import reportlab
    except ImportError:
        print("Installing reportlab...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'reportlab'])
    
    create_indian_bank_statement()
    print("\n📄 Upload this PDF in the Banks section of your app!")