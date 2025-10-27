import React, { useState, useEffect } from 'react';
import bankService from '../../services/bankService';
import { formatCurrency } from '../../utils/formatters';

export default function BankManagement({ onRefresh }) {
  const [banks, setBanks] = useState([]);
  const [statements, setStatements] = useState([]);
  const [showAddBank, setShowAddBank] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const banksData = await bankService.getAll();
      setBanks(banksData);
      
      const statementsData = await bankService.getStatements();
      setStatements(statementsData);
    } catch (error) {
      console.error('Error loading banks:', error);
    }
  };

  const handleAddBank = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      bank_name: formData.get('bank_name'),
      account_number: formData.get('account_number'),
      account_type: formData.get('account_type'),
      balance: parseFloat(formData.get('balance') || 0)
    };

    try {
      await bankService.create(data);
      setShowAddBank(false);
      loadData();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error adding bank:', error);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      setUploadMessage('❌ Please upload a PDF file');
      return;
    }

    setUploading(true);
    setUploadMessage('📄 Processing statement...');

    try {
      const result = await bankService.uploadStatement(file);
      
      if (result.duplicate) {
        setUploadMessage(`⚠️ ${result.message}`);
      } else {
        setUploadMessage(`✅ Success! Added ${result.transactions_added} transactions`);
        loadData();
        if (onRefresh) onRefresh();
      }
    } catch (error) {
      setUploadMessage(`❌ Error: ${error.response?.data?.error || error.message}`);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div>
      <div className="dashboard-header">
        <h1>Bank Accounts</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => setShowAddBank(true)} className="btn-add">
            + Add Bank
          </button>
          <label htmlFor="statement-upload" className="btn-add" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📄 Upload Statement
            <input
              id="statement-upload"
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              disabled={uploading}
            />
          </label>
        </div>
      </div>

      {uploadMessage && (
        <div style={{
          padding: '16px',
          marginBottom: '20px',
          borderRadius: '8px',
          background: uploadMessage.includes('✅') ? '#e8f5e9' : uploadMessage.includes('⚠️') ? '#fff3e0' : '#ffebee',
          color: uploadMessage.includes('✅') ? '#2e7d32' : uploadMessage.includes('⚠️') ? '#f57c00' : '#c62828'
        }}>
          {uploadMessage}
        </div>
      )}

      {/* Bank Accounts */}
      <div className="goals-grid" style={{ marginBottom: '30px' }}>
        {banks.map((bank) => (
          <div key={bank._id} className="goal-card">
            <h3>{bank.bank_name}</h3>
            <div style={{ fontSize: '14px', color: '#666', marginTop: '8px' }}>
              <div>Account: {bank.account_number}</div>
              <div>Type: {bank.account_type}</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#667eea', marginTop: '12px' }}>
                {formatCurrency(bank.balance || 0)}
              </div>
            </div>
          </div>
        ))}

        {banks.length === 0 && (
          <div className="no-data" style={{ gridColumn: '1 / -1' }}>
            No bank accounts added yet. Add one or upload a statement!
          </div>
        )}
      </div>

      {/* Statement Upload History */}
      <div className="card">
        <h2>Upload History</h2>
        <div className="transactions-table">
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                <th style={{ textAlign: 'left', padding: '12px' }}>Date</th>
                <th style={{ textAlign: 'left', padding: '12px' }}>Filename</th>
                <th style={{ textAlign: 'left', padding: '12px' }}>Transactions</th>
                <th style={{ textAlign: 'left', padding: '12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {statements.map((stmt, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '12px' }}>
                    {new Date(stmt.uploaded_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '12px' }}>{stmt.filename}</td>
                  <td style={{ padding: '12px' }}>{stmt.transactions_count}</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      background: '#e8f5e9',
                      color: '#2e7d32'
                    }}>
                      {stmt.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {statements.length === 0 && (
            <div className="no-data">No statements uploaded yet</div>
          )}
        </div>
      </div>

      {/* Add Bank Modal */}
      {showAddBank && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Add Bank Account</h2>
            <form onSubmit={handleAddBank}>
              <div className="form-group">
                <label>Bank Name</label>
                <input type="text" name="bank_name" required placeholder="e.g., Chase, Bank of America" />
              </div>
              <div className="form-group">
                <label>Account Number (Last 4 digits)</label>
                <input type="text" name="account_number" required placeholder="****1234" />
              </div>
              <div className="form-group">
                <label>Account Type</label>
                <select name="account_type" required>
                  <option value="Checking">Checking</option>
                  <option value="Savings">Savings</option>
                  <option value="Credit Card">Credit Card</option>
                </select>
              </div>
              <div className="form-group">
                <label>Current Balance</label>
                <input type="number" name="balance" step="0.01" placeholder="0.00" />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>
                  Add Bank
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddBank(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}