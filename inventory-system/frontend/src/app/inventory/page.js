'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function InventoryPage() {
  const [inventory, setInventory] = useState([]);
  const [locations, setLocations] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [showIssueModal, setShowIssueModal] = useState(false);

  // Form states
  const [receiveForm, setReceiveForm] = useState({
    product_id: '',
    location_id: '',
    quantity: '',
    unit_cost: '',
    lot_number: '',
    performed_by: ''
  });

  const [issueForm, setIssueForm] = useState({
    product_id: '',
    location_id: '',
    quantity: '',
    reason: '',
    performed_by: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [invRes, locRes, prodRes] = await Promise.all([
        api.getInventory(),
        api.getLocations(),
        api.getProducts()
      ]);
      setInventory(invRes.data || []);
      setLocations(locRes.data || []);
      setProducts(prodRes.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleReceive(e) {
    e.preventDefault();
    try {
      await api.receiveStock({
        ...receiveForm,
        quantity: parseFloat(receiveForm.quantity),
        unit_cost: parseFloat(receiveForm.unit_cost)
      });
      setShowReceiveModal(false);
      setReceiveForm({ product_id: '', location_id: '', quantity: '', unit_cost: '', lot_number: '', performed_by: '' });
      loadData();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }

  async function handleIssue(e) {
    e.preventDefault();
    try {
      await api.issueStock({
        ...issueForm,
        quantity: parseFloat(issueForm.quantity)
      });
      setShowIssueModal(false);
      setIssueForm({ product_id: '', location_id: '', quantity: '', reason: '', performed_by: '' });
      loadData();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }

  if (loading) return <div className="p-8 text-center">Loading inventory...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Inventory Management</h1>
        <div className="space-x-3">
          <button
            onClick={() => setShowReceiveModal(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            + Receive Stock
          </button>
          <button
            onClick={() => setShowIssueModal(true)}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
          >
            - Issue Stock
          </button>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Quantity</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Reserved</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reorder Point</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {inventory.map((item) => {
              const qty = parseFloat(item.quantity);
              const reorder = parseFloat(item.Product?.reorder_point || 0);
              const threshold = reorder * 0.15;
              const isCritical = qty <= threshold && reorder > 0;
              const isWarning = qty <= reorder && qty > threshold;

              return (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{item.Product?.name}</div>
                    <div className="text-sm text-gray-500">{item.Product?.sku}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{item.Location?.name}</td>
                  <td className="px-6 py-4 text-right font-medium">{qty.toLocaleString()}</td>
                  <td className="px-6 py-4 text-right text-gray-500">{item.reserved_quantity}</td>
                  <td className="px-6 py-4 text-sm">{reorder.toLocaleString()}</td>
                  <td className="px-6 py-4">
                    {isCritical ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">CRITICAL</span>
                    ) : isWarning ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">LOW</span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">OK</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Receive Modal */}
      {showReceiveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Receive Stock</h2>
            <form onSubmit={handleReceive} className="space-y-4">
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={receiveForm.product_id}
                onChange={(e) => setReceiveForm({...receiveForm, product_id: e.target.value})}
                required
              >
                <option value="">Select Product</option>
                {products.map(p => <option key={p.id} value={p.id}>{p.sku} - {p.name}</option>)}
              </select>
              
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={receiveForm.location_id}
                onChange={(e) => setReceiveForm({...receiveForm, location_id: e.target.value})}
                required
              >
                <option value="">Select Location</option>
                {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
              
              <input
                type="number"
                step="0.001"
                placeholder="Quantity"
                className="w-full border rounded-lg px-3 py-2"
                value={receiveForm.quantity}
                onChange={(e) => setReceiveForm({...receiveForm, quantity: e.target.value})}
                required
              />
              
              <input
                type="number"
                step="0.0001"
                placeholder="Unit Cost"
                className="w-full border rounded-lg px-3 py-2"
                value={receiveForm.unit_cost}
                onChange={(e) => setReceiveForm({...receiveForm, unit_cost: e.target.value})}
                required
              />
              
              <input
                type="text"
                placeholder="Lot Number (optional)"
                className="w-full border rounded-lg px-3 py-2"
                value={receiveForm.lot_number}
                onChange={(e) => setReceiveForm({...receiveForm, lot_number: e.target.value})}
              />
              
              <input
                type="text"
                placeholder="Performed By"
                className="w-full border rounded-lg px-3 py-2"
                value={receiveForm.performed_by}
                onChange={(e) => setReceiveForm({...receiveForm, performed_by: e.target.value})}
                required
              />
              
              <div className="flex gap-3 pt-4">
                <button type="submit" className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700">
                  Receive
                </button>
                <button type="button" onClick={() => setShowReceiveModal(false)} className="flex-1 border py-2 rounded-lg hover:bg-gray-50">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Issue Modal */}
      {showIssueModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Issue Stock</h2>
            <form onSubmit={handleIssue} className="space-y-4">
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={issueForm.product_id}
                onChange={(e) => setIssueForm({...issueForm, product_id: e.target.value})}
                required
              >
                <option value="">Select Product</option>
                {products.map(p => <option key={p.id} value={p.id}>{p.sku} - {p.name}</option>)}
              </select>
              
              <select
                className="w-full border rounded-lg px-3 py-2"
                value={issueForm.location_id}
                onChange={(e) => setIssueForm({...issueForm, location_id: e.target.value})}
                required
              >
                <option value="">Select Location</option>
                {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
              
              <input
                type="number"
                step="0.001"
                placeholder="Quantity"
                className="w-full border rounded-lg px-3 py-2"
                value={issueForm.quantity}
                onChange={(e) => setIssueForm({...issueForm, quantity: e.target.value})}
                required
              />
              
              <input
                type="text"
                placeholder="Reason"
                className="w-full border rounded-lg px-3 py-2"
                value={issueForm.reason}
                onChange={(e) => setIssueForm({...issueForm, reason: e.target.value})}
              />
              
              <input
                type="text"
                placeholder="Performed By"
                className="w-full border rounded-lg px-3 py-2"
                value={issueForm.performed_by}
                onChange={(e) => setIssueForm({...issueForm, performed_by: e.target.value})}
                required
              />
              
              <div className="flex gap-3 pt-4">
                <button type="submit" className="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700">
                  Issue
                </button>
                <button type="button" onClick={() => setShowIssueModal(false)} className="flex-1 border py-2 rounded-lg hover:bg-gray-50">
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
