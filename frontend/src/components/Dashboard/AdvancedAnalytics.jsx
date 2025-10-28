import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../../services/api';
import { formatCurrency } from '../../utils/formatters';

export default function AdvancedAnalytics() {
    const [trends, setTrends] = useState([]);
    const [healthScore, setHealthScore] = useState(null);
    const [recommendations, setRecommendations] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAnalytics();
    }, []);

    const loadAnalytics = async () => {
        try {
            const [trendsRes, scoreRes, budgetRes] = await Promise.all([
                api.get('/analytics/spending-trends'),
                api.get('/analytics/financial-health-score'),
                api.get('/analytics/budget-recommendations')
            ]);

            setTrends(trendsRes.data);
            setHealthScore(scoreRes.data);
            setRecommendations(budgetRes.data);
        } catch (error) {
            console.error('Error loading analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="card">Loading advanced analytics...</div>;
    }

    return (
        <div>
            <div className="dashboard-header">
                <h1>Advanced Analytics</h1>
            </div>

            {/* Financial Health Score */}
            {healthScore && (
                <div className="card" style={{ marginBottom: '20px' }}>
                    <h2>Financial Health Score</h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '40px', marginTop: '20px' }}>
                        <div style={{ position: 'relative', width: '200px', height: '200px' }}>
                            <svg width="200" height="200">
                                <circle cx="100" cy="100" r="80" fill="none" stroke="#e0e0e0" strokeWidth="20" />
                                <circle
                                    cx="100"
                                    cy="100"
                                    r="80"
                                    fill="none"
                                    stroke={healthScore.score >= 80 ? '#4caf50' : healthScore.score >= 60 ? '#ff9800' : '#f44336'}
                                    strokeWidth="20"
                                    strokeDasharray={`${(healthScore.score / 100) * 502} 502`}
                                    strokeLinecap="round"
                                    transform="rotate(-90 100 100)"
                                />
                            </svg>
                            <div style={{
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                transform: 'translate(-50%, -50%)',
                                textAlign: 'center'
                            }}>
                                <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#667eea' }}>
                                    {healthScore.score}
                                </div>
                                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#888' }}>
                                    Grade {healthScore.grade}
                                </div>
                            </div>
                        </div>

                        <div style={{ flex: 1 }}>
                            <h3>{healthScore.message}</h3>
                            <div style={{ marginTop: '16px' }}>
                                {healthScore.factors.map((factor, idx) => (
                                    <div key={idx} style={{ marginBottom: '12px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span>{factor.name}</span>
                                            <span style={{ fontWeight: 'bold', color: '#667eea' }}>
                                                {factor.points} pts - {factor.status}
                                            </span>
                                        </div>
                                        <div style={{
                                            width: '100%',
                                            height: '8px',
                                            background: '#e0e0e0',
                                            borderRadius: '4px',
                                            overflow: 'hidden'
                                        }}>
                                            <div style={{
                                                width: `${(factor.points / 40) * 100}%`,
                                                height: '100%',
                                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                                            }}></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Spending Trends */}
            <div className="card" style={{ marginBottom: '20px' }}>
                <h2>12-Month Spending Trends</h2>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={trends}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip formatter={(value) => formatCurrency(value)} />
                        <Legend />
                        <Line type="monotone" dataKey="income" stroke="#4caf50" strokeWidth={3} name="Income" />
                        <Line type="monotone" dataKey="expense" stroke="#f44336" strokeWidth={3} name="Expense" />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Budget Recommendations */}
            {recommendations && (
                <div className="content-grid">
                    <div className="card">
                        <h2>Budget Analysis</h2>
                        <div style={{ marginTop: '20px' }}>
                            <div style={{ marginBottom: '20px' }}>
                                <div style={{ fontSize: '14px', color: '#888', marginBottom: '4px' }}>Total Income</div>
                                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#4caf50' }}>
                                    {formatCurrency(recommendations.analysis.total_income)}
                                </div>
                            </div>
                            <div style={{ marginBottom: '20px' }}>
                                <div style={{ fontSize: '14px', color: '#888', marginBottom: '4px' }}>Total Expense</div>
                                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#f44336' }}>
                                    {formatCurrency(recommendations.analysis.total_expense)}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '14px', color: '#888', marginBottom: '4px' }}>Savings Potential</div>
                                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#667eea' }}>
                                    {formatCurrency(recommendations.analysis.savings_potential)}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <h2>Category-wise Budget Status</h2>
                        <div style={{ marginTop: '20px' }}>
                            {Object.entries(recommendations.analysis.recommendations).map(([category, data], idx) => (
                                <div key={idx} style={{ marginBottom: '16px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                        <span style={{ fontWeight: '500' }}>{category}</span>
                                        <span style={{
                                            fontSize: '12px',
                                            padding: '2px 8px',
                                            borderRadius: '12px',
                                            background: data.status === 'under' ? '#e8f5e9' : '#ffebee',
                                            color: data.status === 'under' ? '#2e7d32' : '#c62828'
                                        }}>
                                            {data.status === 'under' ? 'Within Budget' : 'Over Budget'}
                                        </span>
                                    </div>
                                    <div style={{ fontSize: '14px', color: '#666', marginBottom: '4px' }}>
                                        Actual: {formatCurrency(data.actual)} | Recommended: {formatCurrency(data.recommended)}
                                    </div>
                                    <div style={{
                                        width: '100%',
                                        height: '8px',
                                        background: '#e0e0e0',
                                        borderRadius: '4px',
                                        overflow: 'hidden'
                                    }}>
                                        <div style={{
                                            width: `${Math.min((data.actual / data.recommended) * 100, 100)}%`,
                                            height: '100%',
                                            background: data.status === 'under' ? '#4caf50' : '#f44336'
                                        }}></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Smart Suggestions */}
            {recommendations && recommendations.suggestions.length > 0 && (
                <div className="card" style={{ marginTop: '20px' }}>
                    <h2>💡 Smart Suggestions</h2>
                    <div style={{ marginTop: '20px' }}>
                        {recommendations.suggestions.map((suggestion, idx) => (
                            <div key={idx} style={{
                                padding: '16px',
                                marginBottom: '12px',
                                borderRadius: '8px',
                                background: suggestion.type === 'warning' ? '#fff3e0' : '#e8f5e9',
                                border: `1px solid ${suggestion.type === 'warning' ? '#ff9800' : '#4caf50'}`
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <span style={{ fontSize: '32px' }}>
                                        {suggestion.type === 'warning' ? '⚠️' : '💰'}
                                    </span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                                            {suggestion.category}
                                        </div>
                                        <div style={{ fontSize: '14px', marginBottom: '4px' }}>
                                            {suggestion.message}
                                        </div>
                                        <div style={{ fontSize: '13px', color: '#666', fontStyle: 'italic' }}>
                                            💡 {suggestion.action}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}