import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { formatCurrency } from '../../utils/formatters';

export default function SavingsWidget() {
  const [suggestions, setSuggestions] = useState(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [suggestionsRes, alertsRes] = await Promise.all([
        api.get('/analytics/savings-suggestions'),
        api.get('/analytics/alerts')
      ]);
      setSuggestions(suggestionsRes.data);
      setAlerts(alertsRes.data);
    } catch (error) {
      console.error('Error loading savings data:', error);
    }
  };

  if (!suggestions) return null;

  return (
    <div className="content-grid" style={{ marginBottom: '20px' }}>
      {/* Savings Potential */}
      <div className="card">
        <h2>💰 Savings Potential</h2>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <div style={{ fontSize: '14px', color: '#888', marginBottom: '8px' }}>
            You could save up to
          </div>
          <div style={{ fontSize: '48px', fontWeight: 'bold', color: '#4caf50', marginBottom: '8px' }}>
            {formatCurrency(suggestions.total_potential_savings)}
          </div>
          <div style={{ fontSize: '14px', color: '#888' }}>
            per month ({formatCurrency(suggestions.annual_potential)}/year)
          </div>
        </div>

        <div style={{ marginTop: '20px' }}>
          <h3 style={{ fontSize: '16px', marginBottom: '12px' }}>💡 Quick Wins:</h3>
          {suggestions.suggestions.slice(0, 3).map((suggestion, idx) => (
            <div key={idx} style={{
              padding: '12px',
              marginBottom: '8px',
              borderRadius: '8px',
              background: suggestion.priority === 'high' ? '#fff3e0' : '#f5f5f5',
              borderLeft: `4px solid ${suggestion.priority === 'high' ? '#ff9800' : '#4caf50'}`
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                {suggestion.category} - Save {formatCurrency(suggestion.potential_saving)}
              </div>
              <div style={{ fontSize: '13px', color: '#666' }}>
                {suggestion.tip}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Alerts */}
      <div className="card">
        <h2>🔔 Spending Alerts</h2>
        {alerts.length > 0 ? (
          <div style={{ marginTop: '20px' }}>
            {alerts.slice(0, 5).map((alert, idx) => (
              <div key={idx} style={{
                padding: '12px',
                marginBottom: '8px',
                borderRadius: '8px',
                background: alert.severity === 'warning' ? '#ffebee' : '#e3f2fd',
                borderLeft: `4px solid ${alert.severity === 'warning' ? '#f44336' : '#2196f3'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span>{alert.severity === 'warning' ? '⚠️' : 'ℹ️'}</span>
                  <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                    {alert.message}
                  </div>
                </div>
                <div style={{ fontSize: '13px', color: '#666', marginLeft: '24px' }}>
                  {alert.suggestion}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>✅</div>
            <div>No alerts! Your spending is on track.</div>
          </div>
        )}
      </div>
    </div>
  );
}