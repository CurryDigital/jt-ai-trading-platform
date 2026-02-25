'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      const [summaryRes, alertsRes] = await Promise.all([
        api.getInventorySummary(),
        api.getAlerts()
      ]);
      
      setSummary(summaryRes.data);
      setAlerts(alertsRes.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="p-8 text-center">Loading dashboard...</div>;
  if (error) return <div className="p-8 text-center text-red-600">Error: {error}</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm font-medium text-gray-600">Total Products</p>
          <p className="text-3xl font-bold text-gray-900">{summary?.total_products || 0}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm font-medium text-gray-600">Locations</p>
          <p className="text-3xl font-bold text-gray-900">{summary?.total_locations || 0}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm font-medium text-gray-600">Total Stock</p>
          <p className="text-3xl font-bold text-gray-900">{summary?.total_quantity?.toLocaleString() || 0}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm font-medium text-gray-600">Low Stock Alerts</p>
          <p className={`text-3xl font-bold ${(summary?.alerts?.critical || 0) > 0 ? 'text-red-600' : 'text-gray-900'}`}>
            {summary?.alerts?.critical || 0}
          </p>
        </div>
      </div>

      {/* Alerts Section */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Stock Alerts</h2>
          <div className="mt-2 flex gap-4 text-sm">
            <span className="text-red-600 font-medium">🔴 Critical: {summary?.alerts?.critical || 0}</span>
            <span className="text-yellow-600 font-medium">🟡 Warning: {summary?.alerts?.warning || 0}</span>
          </div>
        </div>
        
        <div className="divide-y divide-gray-200">
          {alerts.length === 0 ? (
            <p className="px-6 py-4 text-gray-500">No alerts at this time. All stock levels are healthy.</p>
          ) : (
            alerts.slice(0, 10).map((alert) => (
              <div key={alert.inventory_id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{alert.product_name}</p>
                    <p className="text-sm text-gray-500">SKU: {alert.product_sku} | Location: {alert.location_name}</p>
                    <p className="text-sm mt-1">
                      Current: <span className="font-semibold">{alert.current_quantity}</span>{' '}
                      | Threshold: {alert.threshold_value} | Reorder: {alert.reorder_point}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      alert.severity === 'CRITICAL' 
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {alert.severity}
                    </span>
                    <p className="text-sm text-gray-500 mt-1">
                      Suggest: Order {alert.suggested_order_qty} {alert.unit_of_measure}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
