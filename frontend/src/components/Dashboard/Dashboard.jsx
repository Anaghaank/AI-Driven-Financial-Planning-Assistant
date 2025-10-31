import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { transactionService } from '../../services/transactionService';
import aiService from '../../services/aiService';
import { authService } from '../../services/authService';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import BankManagement from './BankManagement';
import { formatCurrency } from '../../utils/formatters';
import AdvancedAnalytics from './AdvancedAnalytics';
import api from '../../api';
import SavingsWidget from './SavingsWidget';

export default function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState({ income: 0, expense: 0, balance: 0 });
  const [predictions, setPredictions] = useState(null);
  const [insights, setInsights] = useState('');
  const [showAddTransaction, setShowAddTransaction] = useState(false);
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [activeView, setActiveView] = useState('dashboard');
  const [categoryData, setCategoryData] = useState([]);
  const [monthlyData, setMonthlyData] = useState([]);
  const navigate = useNavigate();

  const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a'];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const txns = await transactionService.getAll();
      setTransactions(txns);

      const totalIncome = txns.filter(t => t.type === 'income').reduce((sum, t) => sum + t.amount, 0);
      const totalExpense = txns.filter(t => t.type === 'expense').reduce((sum, t) => sum + t.amount, 0);

      setStats({
        income: totalIncome,
        expense: totalExpense,
        balance: totalIncome - totalExpense
      });

      // Process category data for pie chart
      const categories = {};
      txns.filter(t => t.type === 'expense').forEach(t => {
        categories[t.category] = (categories[t.category] || 0) + t.amount;
      });

      const categoryArray = Object.entries(categories).map(([name, value]) => ({
        name,
        value: parseFloat(value.toFixed(2))
      }));
      setCategoryData(categoryArray);

      // Process monthly data
      const months = {};
      txns.forEach(t => {
        const date = new Date(t.date);
        const monthKey = `${date.getMonth() + 1}/${date.getFullYear()}`;
        if (!months[monthKey]) {
          months[monthKey] = { month: monthKey, income: 0, expense: 0 };
        }
        if (t.type === 'income') {
          months[monthKey].income += t.amount;
        } else {
          months[monthKey].expense += t.amount;
        }
      });

      const monthlyArray = Object.values(months).slice(-6);
      setMonthlyData(monthlyArray);

      // Load AI data
      // Load AI data - Always call, backend handles errors gracefully
      try {
        const pred = await aiService.getPredictions();
        console.log('Predictions received:', pred);
        setPredictions(pred);
      } catch (error) {
        console.error('Predictions error:', error);
        setPredictions({
          next_month_prediction: 0,
          based_on_days: 0,
          message: 'Add more transactions for predictions'
        });
      }

      try {
        const ins = await aiService.getInsights();
        console.log('Insights received:', ins);
        setInsights(ins.insights || 'Add transactions to see insights!');
      } catch (error) {
        console.error('Insights error:', error);
        setInsights('Add transactions to see your spending analysis!');
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const handleAddTransaction = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      amount: parseFloat(formData.get('amount')),
      category: formData.get('category'),
      description: formData.get('description'),
      type: formData.get('type'),
      date: new Date().toISOString()
    };

    try {
      await transactionService.create(data);
      setShowAddTransaction(false);
      loadData();
    } catch (error) {
      console.error('Error adding transaction:', error);
    }
  };

  const handleAskAI = async (e) => {
    e.preventDefault();
    if (!aiQuery.trim()) {
      setAiResponse('Please enter a question!');
      return;
    }

    setAiResponse('Getting advice...');

    try {
      console.log('Sending AI query:', aiQuery);
      const response = await aiService.getAdvice(aiQuery);
      console.log('AI response received:', response);

      if (response && response.advice) {
        setAiResponse(response.advice);
      } else {
        setAiResponse('No response received. Please try again.');
      }
    } catch (error) {
      console.error('AI advice error:', error);
      setAiResponse(`Error: ${error.message}. Please check if the backend is running.`);
    }
  };

  const renderContent = () => {
    if (activeView === 'transactions') {
      return <TransactionsView transactions={transactions} onRefresh={loadData} />;
    } else if (activeView === 'goals') {
      return <GoalsView onRefresh={loadData} />;
    } else if (activeView === 'banks') {
      return <BankManagement onRefresh={loadData} />;
    } else if (activeView === 'analytics') {
      return <AdvancedAnalytics />;
    }
    return (
      <>
        <div className="dashboard-header">
          <h1>Financial Dashboard</h1>
          <button onClick={() => setShowAddTransaction(true)} className="btn-add">
            + Add Transaction
          </button>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Balance</h3>
            <div className="stat-value">{formatCurrency(stats.balance)}</div>
            <div className={`stat-change ${stats.balance >= 0 ? 'positive' : 'negative'}`}>
              {stats.balance >= 0 ? '↑ Positive' : '↓ Negative'}
            </div>
          </div>

          <div className="stat-card">
            <h3>Total Income</h3>
            <div className="stat-value">{formatCurrency(stats.income)}</div>
            <div style={{ fontSize: '14px', color: '#888', marginTop: '8px' }}>This month</div>
          </div>

          <div className="stat-card">
            <h3>Total Expense</h3>
            <div className="stat-value">{formatCurrency(stats.expense)}</div>
            <div style={{ fontSize: '14px', color: '#888', marginTop: '8px' }}>This month</div>
          </div>
        </div>
        {/* ADD THIS NEW WIDGET */}
        <SavingsWidget />
        {/* Charts */}
        <div className="content-grid">
          <div className="card">
            <h2>Income vs Expense Trend</h2>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="income" stroke="#4caf50" strokeWidth={2} />
                <Line type="monotone" dataKey="expense" stroke="#f44336" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h2>Spending by Category</h2>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: $${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="content-grid">
          {/* Recent Transactions */}
          <div className="card">
            <h2>Recent Transactions</h2>
            <div>
              {transactions.slice(0, 5).map((txn, idx) => (
                <div key={idx} className="transaction-item">
                  <div>
                    <div style={{ fontWeight: '500' }}>{txn.description || txn.category}</div>
                    <div style={{ fontSize: '14px', color: '#888' }}>{txn.category}</div>
                  </div>
                  <div className={`transaction-amount ${txn.type}`}>
                    {txn.type === 'income' ? '+' : '-'}{formatCurrency(txn.amount)}
                  </div>
                </div>
              ))}
              {transactions.length === 0 && (
                <div className="no-data">No transactions yet</div>
              )}
            </div>
          </div>

          {/* AI Insights */}
          <div className="card">
            <h2>AI Insights</h2>
            <div className="insight-box">
              <h3 style={{ marginBottom: '8px' }}>Spending Analysis</h3>
              <p style={{ fontSize: '14px', whiteSpace: 'pre-line' }}>
                {insights || 'Loading insights...'}
              </p>
            </div>

            {predictions && predictions.next_month_prediction && (
              <div className="prediction-box">
                <h3 style={{ marginBottom: '8px' }}>Next Month Prediction</h3>
                <div className="prediction-value">
                  {formatCurrency(predictions.next_month_prediction)}
                </div>
                <p style={{ fontSize: '14px', color: '#666' }}>
                  Based on {predictions.based_on_days || 0} days of data
                </p>
              </div>
            )}
          </div>
        </div>

        {/* AI Assistant */}
        <div className="card ai-assistant">
          <h2>Ask AI Financial Advisor</h2>
          <form onSubmit={handleAskAI}>
            <textarea
              value={aiQuery}
              onChange={(e) => setAiQuery(e.target.value)}
              placeholder="Ask me anything about your finances..."
              rows="3"
            />
            <button type="submit" className="btn-primary">
              Get Advice
            </button>
          </form>
          {aiResponse && (
            <div className="ai-response">
              <h3 style={{ marginBottom: '8px' }}>AI Response:</h3>
              <p style={{ whiteSpace: 'pre-line' }}>{aiResponse}</p>
            </div>
          )}
        </div>
      </>
    );
  };

  return (
    <div className="dashboard-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="logo">F</div>
          <span style={{ fontWeight: 'bold', fontSize: '20px' }}>FinSet</span>
        </div>

        <ul className="sidebar-nav">
          <li
            className={`nav-item ${activeView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveView('dashboard')}
          >
            Dashboard
          </li>
          <li
            className={`nav-item ${activeView === 'transactions' ? 'active' : ''}`}
            onClick={() => setActiveView('transactions')}
          >
            Transactions
          </li>
          <li
            className={`nav-item ${activeView === 'goals' ? 'active' : ''}`}
            onClick={() => setActiveView('goals')}
          >
            Goals
          </li>
          <li
            className={`nav-item ${activeView === 'banks' ? 'active' : ''}`}
            onClick={() => setActiveView('banks')}
          >
            Banks
          </li>
          <li
            className={`nav-item ${activeView === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveView('analytics')}
          >
            Analytics
          </li>
        </ul>

        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {renderContent()}
      </div>

      {/* Add Transaction Modal */}
      {showAddTransaction && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Add Transaction</h2>
            <form onSubmit={handleAddTransaction}>
              <div className="form-group">
                <label>Type</label>
                <select name="type" required>
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>
              <div className="form-group">
                <label>Amount</label>
                <input type="number" name="amount" step="0.01" required />
              </div>
              <div className="form-group">
                <label>Category</label>
                <select name="category" required>
                  <option value="Food & Groceries">Food & Groceries</option>
                  <option value="Shopping">Shopping</option>
                  <option value="Transportation">Transportation</option>
                  <option value="Entertainment">Entertainment</option>
                  <option value="Bills">Bills</option>
                  <option value="Salary">Salary</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Description</label>
                <input type="text" name="description" />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>
                  Add
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddTransaction(false)}
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

// Transactions View Component
function TransactionsView({ transactions, onRefresh }) {
  const [filter, setFilter] = useState('all');

  const filteredTransactions = transactions.filter(t => {
    if (filter === 'all') return true;
    return t.type === filter;
  });

  const handleExport = async (format) => {
    try {
      const response = await api.get(`/export/transactions/${format}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `transactions_${new Date().toISOString().split('T')[0]}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please try again.');
    }
  };

  return (
    <div>
      <div className="dashboard-header">
        <h1>Transactions</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className={filter === 'all' ? 'btn-add' : 'btn-secondary'}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button
            className={filter === 'income' ? 'btn-add' : 'btn-secondary'}
            onClick={() => setFilter('income')}
          >
            Income
          </button>
          <button
            className={filter === 'expense' ? 'btn-add' : 'btn-secondary'}
            onClick={() => setFilter('expense')}
          >
            Expense
          </button>
          <button
            className="btn-secondary"
            onClick={() => handleExport('csv')}
          >
            📄 Export CSV
          </button>
          <button
            className="btn-secondary"
            onClick={() => handleExport('excel')}
          >
            📊 Export Excel
          </button>
        </div>
      </div>

      <div className="card">
        <div className="transactions-table">
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                <th style={{ textAlign: 'left', padding: '12px' }}>Date</th>
                <th style={{ textAlign: 'left', padding: '12px' }}>Description</th>
                <th style={{ textAlign: 'left', padding: '12px' }}>Category</th>
                <th style={{ textAlign: 'left', padding: '12px' }}>Type</th>
                <th style={{ textAlign: 'right', padding: '12px' }}>Amount</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map((txn, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '12px' }}>
                    {new Date(txn.date).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '12px' }}>{txn.description || '-'}</td>
                  <td style={{ padding: '12px' }}>{txn.category}</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      background: txn.type === 'income' ? '#e8f5e9' : '#ffebee',
                      color: txn.type === 'income' ? '#2e7d32' : '#c62828'
                    }}>
                      {txn.type}
                    </span>
                  </td>
                  <td style={{
                    padding: '12px',
                    textAlign: 'right',
                    fontWeight: 'bold',
                    color: txn.type === 'income' ? '#4caf50' : '#f44336'
                  }}>
                    {txn.type === 'income' ? '+' : '-'}{formatCurrency(txn.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredTransactions.length === 0 && (
            <div className="no-data">No transactions found</div>
          )}
        </div>
      </div>
    </div>
  );
}

// Goals View Component
function GoalsView({ onRefresh }) {
  const [goals, setGoals] = useState([]);
  const [banks, setBanks] = useState([]);
  const [showAddGoal, setShowAddGoal] = useState(false);
  const [showAddProgress, setShowAddProgress] = useState(null);
  const [selectedGoal, setSelectedGoal] = useState(null);

  useEffect(() => {
    loadGoals();
    loadBanks();
  }, []);

  const loadGoals = async () => {
    try {
      const response = await api.get('/goals');
      setGoals(response.data);
    } catch (error) {
      console.error('Error loading goals:', error);
    }
  };

  const loadBanks = async () => {
    try {
      const response = await api.get('/banks');
      setBanks(response.data);
    } catch (error) {
      console.error('Error loading banks:', error);
    }
  };

  const handleAddGoal = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      name: formData.get('name'),
      target_amount: parseFloat(formData.get('target_amount')),
      current_amount: 0,
      deadline: formData.get('deadline') || null,
      linked_bank_id: formData.get('linked_bank_id') || null,
      auto_track: formData.get('auto_track') === 'on'
    };

    try {
      await api.post('/goals', data);
      setShowAddGoal(false);
      loadGoals();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error adding goal:', error);
      alert('Failed to create goal. Please try again.');
    }
  };

  const handleAddProgress = async (e, goalId) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const amount = parseFloat(formData.get('amount'));

    try {
      await api.post(`/goals/${goalId}/add-progress`, { amount });
      setShowAddProgress(null);
      loadGoals();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error updating progress:', error);
      alert('Failed to update progress. Please try again.');
    }
  };

  const handleDeleteGoal = async (goalId) => {
    if (!window.confirm('Are you sure you want to delete this goal?')) {
      return;
    }

    try {
      await api.delete(`/goals/${goalId}`);
      loadGoals();
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error deleting goal:', error);
      alert('Failed to delete goal. Please try again.');
    }
  };

  const getStatusColor = (progress) => {
    if (progress >= 100) return '#4caf50';
    if (progress >= 75) return '#8bc34a';
    if (progress >= 50) return '#ff9800';
    if (progress >= 25) return '#ff5722';
    return '#f44336';
  };

  return (
    <div>
      <div className="dashboard-header">
        <h1>💰 Savings Goals</h1>
        <button onClick={() => setShowAddGoal(true)} className="btn-add">
          + Create New Goal
        </button>
      </div>

      {/* Summary Cards */}
      <div className="stats-grid" style={{ marginBottom: '30px' }}>
        <div className="stat-card">
          <h3>Total Goals</h3>
          <div className="stat-value">{goals.length}</div>
        </div>
        <div className="stat-card">
          <h3>Goals Achieved</h3>
          <div className="stat-value">
            {goals.filter(g => g.progress >= 100).length}
          </div>
        </div>
        <div className="stat-card">
          <h3>Total Target</h3>
          <div className="stat-value">
            {formatCurrency(goals.reduce((sum, g) => sum + g.target_amount, 0))}
          </div>
        </div>
        <div className="stat-card">
          <h3>Total Saved</h3>
          <div className="stat-value" style={{ color: '#4caf50' }}>
            {formatCurrency(goals.reduce((sum, g) => sum + (g.current_amount || 0), 0))}
          </div>
        </div>
      </div>

      {/* Goals Grid */}
      <div className="goals-grid">
        {goals.map((goal) => (
          <div key={goal._id} className="goal-card" style={{ position: 'relative' }}>
            {/* Delete Button */}
            <button
              onClick={() => handleDeleteGoal(goal._id)}
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                background: '#ffebee',
                color: '#c62828',
                border: 'none',
                borderRadius: '50%',
                width: '32px',
                height: '32px',
                cursor: 'pointer',
                fontSize: '16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              title="Delete Goal"
            >
              🗑️
            </button>

            <div style={{ marginBottom: '16px' }}>
              <h3 style={{ marginBottom: '8px', fontSize: '20px' }}>{goal.name}</h3>

              {/* Progress Badge */}
              <span style={{
                display: 'inline-block',
                padding: '4px 12px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 'bold',
                background: goal.progress >= 100 ? '#e8f5e9' : '#fff3e0',
                color: goal.progress >= 100 ? '#2e7d32' : '#e65100'
              }}>
                {goal.progress >= 100 ? '✅ Achieved!' : '🎯 In Progress'}
              </span>
            </div>

            {/* Amount Display */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', alignItems: 'baseline' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>Current</div>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#667eea' }}>
                  {formatCurrency(goal.current_amount || 0)}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>Target</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#888' }}>
                  {formatCurrency(goal.target_amount)}
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px', fontWeight: '500' }}>Progress</span>
                <span style={{ fontSize: '14px', fontWeight: 'bold', color: getStatusColor(goal.progress) }}>
                  {goal.progress.toFixed(1)}%
                </span>
              </div>
              <div style={{
                width: '100%',
                height: '12px',
                background: '#e0e0e0',
                borderRadius: '6px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${Math.min(goal.progress, 100)}%`,
                  height: '100%',
                  background: `linear-gradient(90deg, ${getStatusColor(goal.progress)}, ${getStatusColor(goal.progress)}dd)`,
                  transition: 'width 0.5s ease'
                }}></div>
              </div>
            </div>

            {/* Remaining Amount */}
            {goal.progress < 100 && (
              <div style={{
                padding: '8px 12px',
                background: '#f5f5f5',
                borderRadius: '6px',
                marginBottom: '12px',
                fontSize: '14px'
              }}>
                <span style={{ color: '#666' }}>Remaining: </span>
                <span style={{ fontWeight: 'bold', color: '#333' }}>
                  {formatCurrency(goal.target_amount - (goal.current_amount || 0))}
                </span>
              </div>
            )}

            {/* Deadline */}
            {goal.deadline && (
              <div style={{ fontSize: '13px', color: '#666', marginBottom: '12px' }}>
                📅 Deadline: {new Date(goal.deadline).toLocaleDateString('en-IN')}
                {goal.days_remaining !== null && goal.days_remaining !== undefined && (
                  <span style={{
                    marginLeft: '8px',
                    color: goal.days_remaining < 30 ? '#f44336' : '#4caf50'
                  }}>
                    ({goal.days_remaining} days left)
                  </span>
                )}
              </div>
            )}

            {/* Linked Bank */}
            {goal.linked_bank && (
              <div style={{
                fontSize: '12px',
                color: '#667eea',
                marginBottom: '12px',
                padding: '6px 10px',
                background: '#f0f4ff',
                borderRadius: '4px'
              }}>
                🏦 Linked to {goal.linked_bank.bank_name} (****{goal.linked_bank.account_number.slice(-4)})
              </div>
            )}

            {/* Action Button */}
            {goal.progress < 100 && (
              <button
                onClick={() => setShowAddProgress(goal._id)}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '14px'
                }}
              >
                💰 Add Progress
              </button>
            )}

            {/* Add Progress Modal */}
            {showAddProgress === goal._id && (
              <div className="modal-overlay">
                <div className="modal-content">
                  <h2>Add Progress to "{goal.name}"</h2>
                  <form onSubmit={(e) => handleAddProgress(e, goal._id)}>
                    <div className="form-group">
                      <label>Amount to Add</label>
                      <input
                        type="number"
                        name="amount"
                        step="0.01"
                        min="0.01"
                        required
                        placeholder="Enter amount"
                        autoFocus
                      />
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                        Current: {formatCurrency(goal.current_amount || 0)} |
                        Remaining: {formatCurrency(goal.target_amount - (goal.current_amount || 0))}
                      </div>
                    </div>
                    <div className="form-actions">
                      <button type="submit" className="btn-primary" style={{ flex: 1 }}>
                        Add Progress
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowAddProgress(null)}
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
        ))}

        {goals.length === 0 && (
          <div className="no-data" style={{ gridColumn: '1 / -1', padding: '60px 20px' }}>
            <div style={{ fontSize: '64px', marginBottom: '20px' }}>🎯</div>
            <h3>No Savings Goals Yet</h3>
            <p style={{ color: '#666', marginTop: '10px' }}>
              Create your first goal and start saving towards your dreams!
            </p>
          </div>
        )}
      </div>

      {/* Add Goal Modal */}
      {showAddGoal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Create New Savings Goal</h2>
            <form onSubmit={handleAddGoal}>
              <div className="form-group">
                <label>Goal Name *</label>
                <input
                  type="text"
                  name="name"
                  required
                  placeholder="e.g., Emergency Fund, Vacation, New Laptop"
                />
              </div>
              <div className="form-group">
                <label>Target Amount (₹) *</label>
                <input
                  type="number"
                  name="target_amount"
                  step="0.01"
                  min="1"
                  required
                  placeholder="10000"
                />
              </div>
              <div className="form-group">
                <label>Target Deadline (Optional)</label>
                <input
                  type="date"
                  name="deadline"
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>
              <div className="form-group">
                <label>Link to Bank Account (Optional)</label>
                <select name="linked_bank_id">
                  <option value="">-- No Bank Link --</option>
                  {banks.map(bank => (
                    <option key={bank._id} value={bank._id}>
                      {bank.bank_name} - {bank.account_number}
                    </option>
                  ))}
                </select>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                  Link to track progress with your bank balance
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary" style={{ flex: 1 }}>
                  Create Goal
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddGoal(false)}
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