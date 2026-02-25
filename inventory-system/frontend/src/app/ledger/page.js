'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function LedgerPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadLedger();
  }, [page]);

  async function loadLedger() {
    try {
      setLoading(true);
      const res = await api.getLedger({ page, limit: 25 });
      setEntries(res.data || []);
      setTotalPages(res.pages || 1);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function getMovementBadge(type) {
    const styles = {
      RECEIPT: 'bg-green-100 text-green-800',
      ISSUE: 'bg-red-100 text-red-800',
      TRANSFER_IN: 'bg-blue-100 text-blue-800',
      TRANSFER_OUT: 'bg-blue-100 text-blue-800',
      ADJUSTMENT: 'bg-yellow-100 text-yellow-800'
    };
    return styles[type] || 'bg-gray-100 text-gray-800';
  }

  if (loading) return <div className="p-8 text-center">Loading ledger...</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Stock Ledger</h1>
      
      <p className="text-gray-600 mb-4">Immutable audit trail of all stock movements.</p>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Unit Cost</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Balance</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">By</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {entries.map((entry) => (
              <tr key={entry.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-500">
                  {new Date(entry.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{entry.Product?.name}</div>
                  <div className="text-xs text-gray-500">{entry.Location?.name}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getMovementBadge(entry.movement_type)}`}>
                    {entry.movement_type}
                  </span>
                </td>
                <td className={`px-4 py-3 text-right font-medium ${
                  entry.quantity > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {entry.quantity > 0 ? '+' : ''}{entry.quantity}
                </td>
                <td className="px-4 py-3 text-right text-sm">
                  {entry.unit_cost > 0 ? `$${entry.unit_cost}` : '-'}
                </td>
                <td className="px-4 py-3 text-right text-sm">
                  {entry.total_cost ? `$${Math.abs(entry.total_cost).toFixed(2)}` : '-'}
                </td>
                <td className="px-4 py-3 text-right font-medium">
                  {entry.running_balance}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {entry.performed_by}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-4 py-2 border rounded-lg disabled:opacity-50 hover:bg-gray-50"
        >
          Previous
        </button>
        
        <span className="text-gray-600">Page {page} of {totalPages}</span>
        
        <button
          onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          className="px-4 py-2 border rounded-lg disabled:opacity-50 hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}
