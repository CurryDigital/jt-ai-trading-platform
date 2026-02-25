'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState({
    sku: '',
    name: '',
    description: '',
    category: '',
    unit_of_measure: 'EA',
    reorder_point: '',
    max_stock: ''
  });

  useEffect(() => {
    loadProducts();
  }, []);

  async function loadProducts() {
    try {
      setLoading(true);
      const res = await api.getProducts();
      setProducts(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      await api.createProduct({
        ...form,
        reorder_point: parseFloat(form.reorder_point) || 0,
        max_stock: parseFloat(form.max_stock) || 0
      });
      setShowAddModal(false);
      setForm({ sku: '', name: '', description: '', category: '', unit_of_measure: 'EA', reorder_point: '', max_stock: '' });
      loadProducts();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }

  if (loading) return <div className="p-8 text-center">Loading products...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Product Catalog</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
        >
          + Add Product
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">UOM</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Reorder Point</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Max Stock</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {products.map((product) => (
              <tr key={product.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-gray-900">{product.sku}</td>
                <td className="px-6 py-4">{product.name}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{product.category || '-'}</td>
                <td className="px-6 py-4 text-sm">{product.unit_of_measure}</td>
                <td className="px-6 py-4 text-right">{product.reorder_point}</td>
                <td className="px-6 py-4 text-right">{product.max_stock}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                    product.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {product.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Product Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Add New Product</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="text"
                placeholder="SKU *"
                className="w-full border rounded-lg px-3 py-2"
                value={form.sku}
                onChange={(e) => setForm({...form, sku: e.target.value})}
                required
              />
              
              <input
                type="text"
                placeholder="Product Name *"
                className="w-full border rounded-lg px-3 py-2"
                value={form.name}
                onChange={(e) => setForm({...form, name: e.target.value})}
                required
              />
              
              <input
                type="text"
                placeholder="Category"
                className="w-full border rounded-lg px-3 py-2"
                value={form.category}
                onChange={(e) => setForm({...form, category: e.target.value})}
              />
              
              <input
                type="text"
                placeholder="Unit of Measure (EA, KG, L, etc.)"
                className="w-full border rounded-lg px-3 py-2"
                value={form.unit_of_measure}
                onChange={(e) => setForm({...form, unit_of_measure: e.target.value})}
              />
              
              <input
                type="number"
                step="0.001"
                placeholder="Reorder Point"
                className="w-full border rounded-lg px-3 py-2"
                value={form.reorder_point}
                onChange={(e) => setForm({...form, reorder_point: e.target.value})}
              />
              
              <input
                type="number"
                step="0.001"
                placeholder="Max Stock"
                className="w-full border rounded-lg px-3 py-2"
                value={form.max_stock}
                onChange={(e) => setForm({...form, max_stock: e.target.value})}
              />
              
              <textarea
                placeholder="Description"
                className="w-full border rounded-lg px-3 py-2"
                rows="3"
                value={form.description}
                onChange={(e) => setForm({...form, description: e.target.value})}
              />
              
              <div className="flex gap-3 pt-4">
                <button type="submit" className="flex-1 bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700">
                  Add Product
                </button>
                <button type="button" onClick={() => setShowAddModal(false)} className="flex-1 border py-2 rounded-lg hover:bg-gray-50">
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
