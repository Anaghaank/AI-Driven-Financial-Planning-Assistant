import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { formatCurrency } from '../../utils/formatters';

export default function BankManagement({ onRefresh }) {
  const [banks, setBanks] = useState([]);
  const [statements, setStatements] = useState([]);
  const [showAddBank, setShowAddBank] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [banksData, statementsData] = await Promise.all([
        api.get('/banks'),
        api.get('/banks/statements')
      ]);
      setBanks(banksData.data);
      setStatements(statementsData.data);
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
      await api.post('/banks', data);
      setShowAddBank(false);
      loadData();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error adding bank:', error);
      alert('Failed to add bank. Please try again.');
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
    setUploadProgress(0);
    setUploadMessage('📄 Processing statement... This may take a few moments.');

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const result = await api.post('/banks/upload-statement', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (result.data.duplicate) {
        setUploadMessage(`⚠️ ${result.data.message}`);
      } else {
        setUploadMessage(
          `✅ Success! ${result.data.transactions_added} transactions added from ${result.data.bank_info.bank_name}`
        );
        loadData();
        if (onRefresh) onRefresh();
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadMessage(
        `❌ Error: ${error.response?.data?.error || 'Failed to process statement. Please try again.'}`
      );
    } finally {
      setUploading(false);
      setUploadProgress(0);
      e.target.value = '';
      
      // Clear message after 10 seconds
      setTimeout(() => setUploadMessage(''), 10000);
    }
  };

  const totalBalance = banks.reduce((sum, bank) => sum + (bank.balance || 0), 0);

  return (
    <div>
      <div className="dashboard-header">
        <h1>🏦 Bank Accounts</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => setShowAddBank(true)} className="btn-add">
            + Add Bank
          </button>
          <label
            htmlFor="statement-upload"
            className="btn-add"
            style={{
              cursor: uploading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              opacity: uploading ? 0.6 : 1
            }}
          >
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

      {/* Upload Progress */}
      {uploading && (
        <div className="card" style={{ marginBottom: '20px' }}>
          <h3>Processing...</h3>
          <div style={{
            width: '100%',
            height: '8px',
            background: '#e0e0e0',
            borderRadius: '4px',
            overflow: 'hidden',
            marginTop: '10px'
          }}>
            <div style={{
              width: `${uploadProgress}%`,
              height: '100%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              transition: 'width 0.3s'
            }}></div>
          </div>
          <p style={{ marginTop: '8px', fontSize: '14px', color: '#666' }}>
            {uploadProgress}% Complete
          </p>
        </div>
      )}

      {/* Upload Message */}
      {uploadMessage && (
        <div style={{
          padding: '16px',
          marginBottom: '20px',
          borderRadius: '8px',
          background: uploadMessage.includes('✅') ? '#e8f5e9' : 
                      uploadMessage.includes('⚠️') ? '#fff3e0' : '#ffebee',
          color: uploadMessage.includes('✅') ? '#2e7d32' : 
                 uploadMessage.includes('⚠️') ? '#f57c00' : '#c62828',
          border: `1px solid ${uploadMessage.includes('✅') ? '#4caf50' : 
                              uploadMessage.includes('⚠️') ? '#ff9800' : '#f44336'}`
        }}>
          {uploadMessage}
        </div>
      )}

      {/* Total Balance Card */}
      {banks.length > 0 && (
        <div className="stat-card" style={{ marginBottom: '20px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <h3 style={{ color: 'rgba(255,255,255,0.9)' }}>Total Balance Across All Banks</h3>
          <div className="stat-value" style={{ color: 'white', fontSize: '36px' }}>
            {formatCurrency(totalBalance)}
          </div>
          <div style={{ fontSize: '14px', color: 'rgba(255,255,255,0.8)', marginTop: '8px' }}>
            {banks.length} {banks.length === 1 ? 'account' : 'accounts'} connected
          </div>
        </div>
      )}

      {/* Bank Accounts Grid */}
      <div className="goals-grid" style={{ marginBottom: '30px' }}>
        {banks.map((bank) => (
          <div key={bank._id} className="goal-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px' }}>
              <div>
                <h3 style={{ marginBottom: '4px' }}>{bank.bank_name}</h3>
                <div style={{ fontSize: '12px', color: '#888' }}>
                  {bank.account_type} Account
                </div>
              </div>
              <div style={{
                padding: '4px 12px',
                background: '#e8f5e9',
                color: '#2e7d32',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                ✓ Active
              </div>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '14px', color: '#888', marginBottom: '4px' }}>
                Account Number
              </div>
              <div style={{ fontSize: '16px', fontWeight: '500', fontFamily: 'monospace' }}>
                {bank.account_number}
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '14px', color: '#888', marginBottom: '4px' }}>
                Current Balance
              </div>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#667eea' }}>
                {formatCurrency(bank.balance || 0)}
              </div>
            </div>

            {bank.last_statement_date && (
              <div style={{ fontSize: '13px', color: '#666', paddingTop: '12px', borderTop: '1px solid #e0e0e0' }}>
                📅 Last updated: {new Date(bank.last_statement_date).toLocaleDateString('en-IN')}
              </div>
            )}
          </div>
        ))}

        {banks.length === 0 && (
          <div className="no-data" style={{ gridColumn: '1 / -1', padding: '60px 20px' }}>
            <div style={{ fontSize: '64px', marginBottom: '20px' }}>🏦</div>
            <h3>No Bank Accounts Added</h3>
            <p style={{ color: '#666', marginTop: '10px' }}>
              Add a bank account or upload your bank statement to get started!
            </p>
          </div>
        )}
      </div>

      {/* Upload History */}
      <div className="card">
        <h2>📋 Statement Upload History</h2>
        <div className="transactions-table">
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                <th style={{ textAlign: 'left', padding: '12px' }}>Date</th>
                <th style={{ textAlign: 'left', padding: '12px' }}>Filename</th>
                <th style={{ textAlign: 'center', padding: '12px' }}>Transactions</th>
                <th style={{ textAlign: 'center', padding: '12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {statements.map((stmt, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '12px' }}>
                    {new Date(stmt.uploaded_at).toLocaleDateString('en-IN')}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span>📄</span>
                      <span>{stmt.filename}</span>
                    </div>
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold' }}>
                    {stmt.transactions_count}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      background: '#e8f5e9',
                      color: '#2e7d32'
                    }}>
                      ✓ {stmt.status}
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
                <label>Bank Name *</label>
                <select name="bank_name" required>
                  <option value="">-- Select Bank --</option>
                  <option value="State Bank of India">State Bank of India</option>
                  <option value="HDFC Bank">HDFC Bank</option>
                  <option value="ICICI Bank">ICICI Bank</option>
                  <option value="Axis Bank">Axis Bank</option>
                  <option value="Karnataka Bank">Karnataka Bank</option>
                  <option value="Punjab National Bank">Punjab National Bank</option>
                  <option value="Bank of Baroda">Bank of Baroda</option>
                  <option value="Canara Bank">Canara Bank</option>
                  <option value="Kotak Mahindra Bank">Kotak Mahindra Bank</option>
                  <option value="Yes Bank">Yes Bank</option>
                  <option value="IDBI Bank">IDBI Bank</option>
                  <option value="Union Bank">Union Bank</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Account Number (Last 4 digits) *</label>
                <input
                  type="text"
                  name="account_number"
                  required
                  placeholder="****1234"
                  pattern="^\*{4}\d{4}$"
                  title="Enter in format: ****1234"
                />
              </div>
              <div className="form-group">
                <label>Account Type *</label>
                <select name="account_type" required>
                  <option value="Savings">Savings Account</option>
                  <option value="Current">Current Account</option>
                  <option value="Credit Card">Credit Card</option>
                  <option value="Fixed Deposit">Fixed Deposit</option>
                </select>
              </div>
              <div className="form-group">
                <label>Current Balance (₹)</label>
                <input
                  type="number"
                  name="balance"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>
                  Add Bank Account
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