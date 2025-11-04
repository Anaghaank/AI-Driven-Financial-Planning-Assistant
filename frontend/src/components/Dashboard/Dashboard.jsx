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
  const [darkMode, setDarkMode] = useState(() => {
    // Load saved theme from localStorage
    return localStorage.getItem('theme') === 'dark';
  });

  const [categoryData, setCategoryData] = useState([]);
  const [monthlyData, setMonthlyData] = useState([]);
  const navigate = useNavigate();

  const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a'];

  useEffect(() => {
    loadData();
  }, []);
  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode);
    localStorage.setItem('theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

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
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ cx, cy, midAngle, innerRadius, outerRadius, percent, name, value }) => {
                    const RADIAN = Math.PI / 180;
                    const radius = innerRadius + (outerRadius - innerRadius) * 0.55;
                    const x = cx + radius * Math.cos(-midAngle * RADIAN);
                    const y = cy + radius * Math.sin(-midAngle * RADIAN);

                    if (percent < 0.08) return null; // skip small slices

                    return (
                      <text
                        
                        fill={darkMode ? "#f3f4f6" : "#111827"} // 👈 dynamic color
                        textAnchor={x > cx ? "start" : "end"}
                        dominantBaseline="central"
                        fontSize={12}
                        fontWeight={500}
                      >
                        {`${name}: ₹${value}`}
                      </text>
                    );
                  }}
                  outerRadius={90}
                  innerRadius={45}
                  dataKey="value"
                  stroke={darkMode ? "#111827" : "#fff"}
                  strokeWidth={2}
                >
                  {categoryData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                      style={{ filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.15))" }}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: darkMode ? "#2a2a44" : "#f9fafb",
                    borderRadius: "8px",
                    border: "1px solid #ddd",
                    color: darkMode ? "#fff" : "#111827",
                  }}
                  formatter={(value, name) => [`₹${value}`, name]}
                />
                <Legend
                  layout="horizontal"
                  verticalAlign="bottom"
                  align="center"
                  iconType="circle"
                  wrapperStyle={{
                    fontSize: 12,
                    marginTop: 10,
                    color: darkMode ? "#ddd" : "#444",
                  }}
                />
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
      <div
        className="sidebar"
        style={{
          width: 260,
          background: darkMode ? "#1b1b2f" : "#ffffff",
          color: darkMode ? "#f3f4f6" : "#1f2937",
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          justifyContent: "space-between",
          padding: "24px 20px",
          borderRight: darkMode ? "1px solid #2a2a44" : "1px solid #e5e7eb",
          boxShadow: darkMode
            ? "inset -1px 0 0 rgba(255,255,255,0.05)"
            : "inset -1px 0 0 rgba(0,0,0,0.05)",
          transition: "all 0.3s ease",
        }}
      >
        {/* --- Top Section --- */}
        <div style={{ overflowY: "auto", flexGrow: 1 }}>
          {/* Header */}
          <div
            className="sidebar-header"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 40,
            }}
          >
            <div
              className="logo"
              style={{
                width: 44,
                height: 44,
                background: "linear-gradient(135deg, #667eea, #764ba2)",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "white",
                fontWeight: "bold",
                fontSize: 20,
                boxShadow: "0 3px 6px rgba(118, 75, 162, 0.3)",
              }}
            >
              F
            </div>
            <span
              style={{
                fontWeight: 700,
                fontSize: 22,
                letterSpacing: "0.5px",
                color: darkMode ? "#e5e7eb" : "#1f2937",
              }}
            >
              FinSet
            </span>
          </div>

          {/* Navigation */}
          <ul className="sidebar-nav" style={{ listStyle: "none", padding: 0 }}>
            {[
              { id: "dashboard", label: "Dashboard", icon: "📊" },
              { id: "transactions", label: "Transactions", icon: "💰" },
              { id: "goals", label: "Goals", icon: "🎯" },
              { id: "banks", label: "Banks", icon: "🏦" },
              { id: "analytics", label: "Analytics", icon: "📈" },
            ].map((item) => (
              <li
                key={item.id}
                className={`nav-item ${activeView === item.id ? "active" : ""}`}
                onClick={() => setActiveView(item.id)}
                style={{
                  padding: "12px 16px",
                  marginBottom: 8,
                  borderRadius: 10,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  background:
                    activeView === item.id
                      ? "linear-gradient(135deg, #667eea, #764ba2)"
                      : darkMode
                        ? "#23233b"
                        : "#f9fafb",
                  color:
                    activeView === item.id
                      ? "#ffffff"
                      : darkMode
                        ? "#d1d5db"
                        : "#374151",
                  fontWeight: 500,
                  transition: "all 0.25s ease",
                }}
                onMouseEnter={(e) => {
                  if (activeView !== item.id)
                    e.currentTarget.style.background = darkMode
                      ? "#2a2a44"
                      : "#f3f4f6";
                }}
                onMouseLeave={(e) => {
                  if (activeView !== item.id)
                    e.currentTarget.style.background = darkMode
                      ? "#23233b"
                      : "#f9fafb";
                }}
              >
                <span style={{ fontSize: 18 }}>{item.icon}</span>
                {item.label}
              </li>
            ))}
          </ul>
        </div>

        {/* --- Bottom Section (Theme Toggle + Logout) --- */}
        {/* --- Bottom Section (Theme Toggle + Logout) --- */}
        {/* --- Bottom Section --- */}
        <div
          style={{
            marginTop: "auto",
            padding: "20px 14px",
            borderTop: darkMode ? "1px solid #2a2a44" : "1px solid #eee",
            display: "flex",
            flexDirection: "column",
            alignItems: "stretch",
            gap: "18px",
            position: "sticky",
            bottom: 0,
            background: darkMode ? "#1e1e2f" : "#fff",
            zIndex: 10,
          }}
        >
          {/* Theme Toggle */}
          <div
            onClick={() => setDarkMode(!darkMode)}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              background: darkMode ? "#2a2a44" : "#f9fafb",
              borderRadius: "12px",
              padding: "10px 14px",
              cursor: "pointer",
              boxShadow: darkMode
                ? "inset 0 0 5px rgba(0,0,0,0.6)"
                : "0 1px 3px rgba(0,0,0,0.08)",
              transition: "all 0.3s ease",
            }}
          >
            <div
              style={{
                position: "relative",
                width: "48px",
                height: "24px",
                borderRadius: "999px",
                background: darkMode ? "#374151" : "#e5e7eb",
                boxShadow: darkMode
                  ? "inset 0 0 6px rgba(0,0,0,0.6)"
                  : "inset 0 0 4px rgba(0,0,0,0.2)",
                transition: "background 0.3s ease",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  top: "2px",
                  left: darkMode ? "25px" : "2px",
                  width: "20px",
                  height: "20px",
                  background: darkMode
                    ? "linear-gradient(145deg, #6366f1, #4338ca)"
                    : "linear-gradient(145deg, #facc15, #fbbf24)",
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "12px",
                  boxShadow: darkMode
                    ? "0 0 6px rgba(99,102,241,0.6)"
                    : "0 0 6px rgba(250,204,21,0.5)",
                  transition: "all 0.3s ease",
                }}
              >
                {darkMode ? "🌙" : "☀️"}
              </div>
            </div>
            <span
              style={{
                fontSize: "13px",
                fontWeight: 600,
                color: darkMode ? "#e5e7eb" : "#374151",
                userSelect: "none",
              }}
            >
              {darkMode ? "Dark Mode" : "Light Mode"}
            </span>
          </div>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              padding: "10px 0",
              borderRadius: "12px",
              border: "none",
              background: darkMode ? "#2a2a44" : "#f3f4f6",
              color: darkMode ? "#f9fafb" : "#374151",
              fontWeight: 600,
              fontSize: "14px",
              cursor: "pointer",
              boxShadow: darkMode
                ? "inset 0 0 4px rgba(0,0,0,0.4)"
                : "0 1px 3px rgba(0,0,0,0.08)",
              transition: "all 0.25s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = darkMode ? "#3a3a5c" : "#e5e7eb";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = darkMode ? "#2a2a44" : "#f3f4f6";
            }}
          >
            <span style={{ fontSize: "16px" }}>🚪</span>
            Logout
          </button>
        </div>


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
// Replace your existing TransactionsView with this component
function TransactionsView({ transactions = [], onRefresh }) {
  const [keyword, setKeyword] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [quick, setQuick] = useState("");
  const [page, setPage] = useState(1);
  const PER_PAGE = 20;

  const [isDark, setIsDark] = useState(false);
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.body.classList.contains("dark-mode"));
    });
    observer.observe(document.body, { attributes: true, attributeFilter: ["class"] });
    setIsDark(document.body.classList.contains("dark-mode"));
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!quick) return;
    const today = new Date();
    let s = "", e = today.toISOString().split("T")[0];
    if (quick === "today") s = e;
    else if (quick === "this_week") {
      const wkStart = new Date(today);
      wkStart.setDate(today.getDate() - today.getDay());
      s = wkStart.toISOString().split("T")[0];
    } else if (quick === "this_month") {
      s = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split("T")[0];
    } else if (quick === "last_30_days") {
      const d = new Date(today);
      d.setDate(today.getDate() - 30);
      s = d.toISOString().split("T")[0];
    }
    setStartDate(s);
    setEndDate(e);
    setPage(1);
  }, [quick]);

  const filtered = transactions.filter((t) => {
    const q = keyword.toLowerCase();
    if (q && !((t.description || "").toLowerCase().includes(q) || (t.category || "").toLowerCase().includes(q))) return false;
    if (typeFilter !== "all" && t.type !== typeFilter) return false;
    if (categoryFilter && t.category !== categoryFilter) return false;
    if (minAmount && t.amount < parseFloat(minAmount)) return false;
    if (maxAmount && t.amount > parseFloat(maxAmount)) return false;
    if (startDate && new Date(t.date) < new Date(startDate)) return false;
    if (endDate && new Date(t.date) > new Date(endDate)) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const pageItems = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  const summary = filtered.reduce(
    (acc, t) => {
      if (t.type === "income") acc.income += t.amount;
      else acc.expense += t.amount;
      acc.count += 1;
      return acc;
    },
    { income: 0, expense: 0, count: 0 }
  );

  const net = summary.income - summary.expense;
  const categories = Array.from(new Set(transactions.map((t) => t.category).filter(Boolean)));

  const aiMessage = (() => {
    if (filtered.length === 0)
      return "No transactions found for the selected filters. Try changing your search or date range.";

    const categoryTotals = {};
    filtered.forEach((txn) => {
      if (txn.type === "expense") {
        categoryTotals[txn.category] = (categoryTotals[txn.category] || 0) + txn.amount;
      }
    });

    const topCategory = Object.entries(categoryTotals).sort((a, b) => b[1] - a[1])[0];
    const savingsRate = summary.income ? ((net / summary.income) * 100).toFixed(1) : 0;

    if (net > 0 && savingsRate >= 30) {
      return `Excellent! You saved ${savingsRate}% of your income this period. Your top spending area was ${topCategory ? topCategory[0] : "miscellaneous"
        } — great control overall.`;
    } else if (net > 0 && savingsRate < 30) {
      return `You're saving ₹${net.toLocaleString()}, but your savings rate is only ${savingsRate}%. Consider reducing ${topCategory ? topCategory[0].toLowerCase() : "discretionary"
        } expenses for better balance.`;
    } else if (net < 0) {
      return `Your expenses exceeded income by ₹${Math.abs(net).toLocaleString()}. Most spending was in ${topCategory ? topCategory[0] : "general"
        } — let's review this category to optimize.`;
    } else {
      return `You're breaking even this period. Try setting aside at least 10% for savings to build stability.`;
    }
  })();

  // 🎨 Theme colors
  const bg = isDark ? "#111827" : "#f9fafb";
  const card = isDark ? "#1f2937" : "#fff";
  const text = isDark ? "#f3f4f6" : "#111827";
  const subtext = isDark ? "#9ca3af" : "#444";
  const border = isDark ? "#374151" : "#e5e7eb";

  return (
    <div style={{ padding: 0, color: text, background: bg, minHeight: "100vh", transition: "all 0.3s ease" }}>
      <h1 style={{ marginBottom: 8 }}>Transactions</h1>

      {/* AI Card */}
      <div
        style={{
          background: isDark ? "#1e3a8a" : "linear-gradient(90deg, #eef2ff, #f5f3ff)",
          padding: 16,
          borderRadius: 12,
          marginBottom: 16,
          marginTop: 16,
          boxShadow: isDark ? "0 0 8px rgba(0,0,0,0.5)" : "0 1px 3px rgba(0,0,0,0.05)",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <div
          style={{
            background: "#4f46e5",
            color: "#fff",
            borderRadius: "50%",
            width: 42,
            height: 42,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 600,
          }}
        >
          AI
        </div>
        <div>
          <div style={{ fontWeight: 600, color: isDark ? "#fff" : "#111827" }}>AI Financial Assistant</div>
          <div style={{ color: subtext, marginTop: 4, fontSize: 14 }}>{aiMessage}</div>
        </div>
      </div>

      {/* Filters */}
      <div
        style={{
          background: card,
          color: text,
          padding: 14,
          borderRadius: 10,
          display: "flex",
          gap: 10,
          alignItems: "center",
          flexWrap: "wrap",
          boxShadow: isDark ? "0 0 6px rgba(0,0,0,0.5)" : "0 1px 2px rgba(0,0,0,0.05)",
        }}
      >
        <input
          type="text"
          placeholder="🔍 Search transactions..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          style={{
            flex: 1,
            padding: "10px 12px",
            border: `1px solid ${border}`,
            borderRadius: 8,
            fontSize: 14,
            minWidth: 220,
            background: isDark ? "#111827" : "#fff",
            color: text,
          }}
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            border: `1px solid ${border}`,
            background: isDark ? "#111827" : "#fff",
            color: text,
          }}
        >
          <option value="all">All Types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            border: `1px solid ${border}`,
            background: isDark ? "#111827" : "#fff",
            color: text,
          }}
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat}>{cat}</option>
          ))}
        </select>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            border: `1px solid ${border}`,
            background: isDark ? "#111827" : "#fff",
            color: text,
          }}
        />
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            border: `1px solid ${border}`,
            background: isDark ? "#111827" : "#fff",
            color: text,
          }}
        />
        <button
          onClick={() => {
            setKeyword("");
            setTypeFilter("all");
            setCategoryFilter("");
            setMinAmount("");
            setMaxAmount("");
            setStartDate("");
            setEndDate("");
            setQuick("");
          }}
          style={{
            padding: "10px 14px",
            borderRadius: 8,
            border: `1px solid ${border}`,
            background: isDark ? "#8898aeff" : "#f9fafb",
            color: text,
            cursor: "pointer",
          }}
        >
          Reset
        </button>
      </div>

      {/* Table */}
      <div
        style={{
          marginTop: 20,
          background: card,
          borderRadius: 10,
          overflow: "hidden",
          boxShadow: isDark ? "0 0 8px rgba(0,0,0,0.6)" : "0 1px 3px rgba(0,0,0,0.05)",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse", color: text }}>
          <thead>
            <tr style={{ background: isDark ? "#839ab8ff" : "#f9fafb" }}>
              <th style={{ textAlign: "left", padding: 10 }}>Date</th>
              <th style={{ textAlign: "left", padding: 10 }}>Description</th>
              <th style={{ textAlign: "left", padding: 10 }}>Category</th>
              <th style={{ textAlign: "left", padding: 10 }}>Type</th>
              <th style={{ textAlign: "right", padding: 10 }}>Amount</th>
            </tr>
          </thead>
          <tbody>
            {pageItems.map((t, i) => (
              <tr key={t._id || i} style={{ borderTop: `1px solid ${border}` }}>
                <td style={{ padding: 10 }}>{new Date(t.date).toLocaleDateString()}</td>
                <td style={{ padding: 10 }}>{t.description}</td>
                <td style={{ padding: 10 }}>{t.category}</td>
                <td style={{ padding: 10, color: t.type === "income" ? "#16a34a" : "#dc2626", fontWeight: 600 }}>{t.type}</td>
                <td
                  style={{
                    padding: 10,
                    textAlign: "right",
                    color: t.type === "income" ? "#16a34a" : "#dc2626",
                    fontWeight: 700,
                  }}
                >
                  {t.type === "income" ? "+" : "-"}₹{t.amount.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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