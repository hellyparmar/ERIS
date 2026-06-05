import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'

// Defensive helpers for currency formatting
const fmtINR = (v: any) => v == null || isNaN(v) ? '—' : '₹' + Number(v).toLocaleString('en-IN')

const Inventory: React.FC = () => {
  const [searchTerm, setSearchTerm] = React.useState('')

  const products = [
    { id: '1', name: 'Coffee', sku: 'SKU001', category: 'Beverages', price: 150, stock: 45, status: 'In Stock' },
    { id: '2', name: 'Tea', sku: 'SKU002', category: 'Beverages', price: 100, stock: 82, status: 'In Stock' },
    { id: '3', name: 'Snacks', sku: 'SKU003', category: 'Food', price: 50, stock: 15, status: 'Low Stock' },
    { id: '4', name: 'Desserts', sku: 'SKU004', category: 'Food', price: 200, stock: 8, status: 'Critical' },
    { id: '5', name: 'Juice', sku: 'SKU005', category: 'Beverages', price: 80, stock: 120, status: 'In Stock' },
  ]

  const getStockStatus = (stock: number) => {
    if (stock < 20) return 'text-red-600 bg-red-50'
    if (stock < 50) return 'text-yellow-600 bg-yellow-50'
    return 'text-green-600 bg-green-50'
  }

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.sku.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Inventory</h1>
          <p className="text-gray-600 mt-1">Manage your product catalog and stock levels</p>
        </div>
        <Button>Add Product</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Products</CardTitle>
          <CardDescription>{filteredProducts.length} products in catalog</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <Input
              placeholder="Search by product name or SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 font-semibold">Product</th>
                  <th className="text-left py-3 font-semibold">SKU</th>
                  <th className="text-left py-3 font-semibold">Category</th>
                  <th className="text-right py-3 font-semibold">Price</th>
                  <th className="text-right py-3 font-semibold">Stock</th>
                  <th className="text-center py-3 font-semibold">Status</th>
                  <th className="text-center py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((product) => (
                  <tr key={product.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 font-medium">{product.name}</td>
                    <td className="py-3 text-gray-600">{product.sku}</td>
                    <td className="py-3">{product.category}</td>
                    <td className="text-right">{fmtINR(product.price)}</td>
                    <td className={`text-right font-semibold ${getStockStatus(product.stock)}`}>
                      {product.stock}
                    </td>
                    <td className="text-center">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStockStatus(product.stock)}`}>
                        {product.status}
                      </span>
                    </td>
                    <td className="text-center space-x-2">
                      <Button variant="ghost" size="sm">Edit</Button>
                      <Button variant="secondary" size="sm">Reorder</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Inventory
