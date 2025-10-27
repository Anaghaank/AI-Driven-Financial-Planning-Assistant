import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { transactionService } from '../../services/transactionService';
import aiService from '../../services/aiService';
import { authService } from '../../services/authService';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

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
            <div className="stat-value">${stats.balance.toFixed(2)}</div>
            <div className={`stat-change ${stats.balance >= 0 ? 'positive' : 'negative'}`}>
              {stats.balance >= 0 ? '↑ Positive' : '↓ Negative'}
            </div>
          </div>

          <div className="stat-card">
            <h3>Total Income</h3>
            <div className="stat-value">${stats.income.toFixed(2)}</div>
            <div style={{ fontSize: '14px', color: '#888', marginTop: '8px' }}>This month</div>
          </div>

          <div className="stat-card">
            <h3>Total Expense</h3>
            <div className="stat-value">${stats.expense.toFixed(2)}</div>
            <div style={{ fontSize: '14px', color: '#888', marginTop: '8px' }}>This month</div>
          </div>
        </div>

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
                    {txn.type === 'income' ? '+' : '-'}${txn.amount.toFixed(2)}
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
                  ${predictions.next_month_prediction?.toFixed(2) || '0.00'}
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
                    {txn.type === 'income' ? '+' : '-'}${txn.amount.toFixed(2)}
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
  const [showAddGoal, setShowAddGoal] = useState(false);
  const [showAddProgress, setShowAddProgress] = useState(null);

  useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      const { goalService } = require('../../services/goalService');
      const data = await goalService.getAll();
      setGoals(data);
    } catch (error) {
      console.error('Error loading goals:', error);
    }
  };

  const handleAddGoal = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      name: formData.get('name'),
      target_amount: parseFloat(formData.get('target_amount')),
      current_amount: 0,
      deadline: formData.get('deadline') || null
    };

    try {
      const { goalService } = require('../../services/goalService');
      await goalService.create(data);
      setShowAddGoal(false);
      loadGoals();
    } catch (error) {
      console.error('Error adding goal:', error);
    }
  };

  const handleAddProgress = async (e, goalId) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const amount = parseFloat(formData.get('amount'));

    const goal = goals.find(g => g._id === goalId);
    const newAmount = goal.current_amount + amount;

    try {
      const { goalService } = require('../../services/goalService');
      await goalService.update(goalId, { current_amount: newAmount });
      setShowAddProgress(null);
      loadGoals();
    } catch (error) {
      console.error('Error updating progress:', error);
    }
  };

  return (
    <div>
      <div className="dashboard-header">
        <h1>Savings Goals</h1>
        <button onClick={() => setShowAddGoal(true)} className="btn-add">
          + Add Goal
        </button>
      </div>

      <div className="goals-grid">
        {goals.map((goal) => (
          <div key={goal._id} className="goal-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3>{goal.name}</h3>
              <button
                onClick={() => setShowAddProgress(goal._id)}
                style={{
                  padding: '6px 12px',
                  background: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                + Add
              </button>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#667eea' }}>
                  ${goal.current_amount?.toFixed(2) || '0.00'}
                </span>
                <span style={{ fontSize: '14px', color: '#888' }}>
                  of ${goal.target_amount?.toFixed(2)}
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
                  width: `${Math.min((goal.current_amount / goal.target_amount) * 100, 100)}%`,
                  height: '100%',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  transition: 'width 0.3s'
                }}></div>
              </div>

              <div style={{ textAlign: 'right', marginTop: '4px', fontSize: '14px', color: '#888' }}>
                {((goal.current_amount / goal.target_amount) * 100).toFixed(1)}% Complete
              </div>
            </div>

            {goal.deadline && (
              <div style={{ fontSize: '14px', color: '#888' }}>
                Target Date: {new Date(goal.deadline).toLocaleDateString()}
              </div>
            )}

            {showAddProgress === goal._id && (
              <div className="modal-overlay">
                <div className="modal-content">
                  <h2>Add Progress to {goal.name}</h2>
                  <form onSubmit={(e) => handleAddProgress(e, goal._id)}>
                    <div className="form-group">
                      <label>Amount to Add</label>
                      <input
                        type="number"
                        name="amount"
                        step="0.01"
                        required
                        placeholder="Enter amount"
                      />
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
          <div className="no-data" style={{ gridColumn: '1 / -1' }}>
            No goals yet. Create your first savings goal!
          </div>
        )}
      </div>

      {showAddGoal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Create New Goal</h2>
            <form onSubmit={handleAddGoal}>
              <div className="form-group">
                <label>Goal Name</label>
                <input
                  type="text"
                  name="name"
                  required
                  placeholder="e.g., Emergency Fund, Vacation"
                />
              </div>
              <div className="form-group">
                <label>Target Amount</label>
                <input
                  type="number"
                  name="target_amount"
                  step="0.01"
                  required
                  placeholder="10000"
                />
              </div>
              <div className="form-group">
                <label>Target Date (Optional)</label>
                <input type="date" name="deadline" />
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