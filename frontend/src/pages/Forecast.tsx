import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Select } from '../components/ui/Select'

const forecastData = [
  { date: 'Mar 28', actual: 450, forecast: 420, lower: 380, upper: 460 },
  { date: 'Mar 29', actual: 520, forecast: 480, lower: 430, upper: 530 },
  { date: 'Mar 30', actual: null, forecast: 500, lower: 440, upper: 560 },
  { date: 'Mar 31', actual: null, forecast: 520, lower: 450, upper: 590 },
  { date: 'Apr 1', actual: null, forecast: 510, lower: 440, upper: 580 },
  { date: 'Apr 2', actual: null, forecast: 530, lower: 460, upper: 600 },
]

const Forecast: React.FC = () => {
  const [selectedProduct, setSelectedProduct] = React.useState('coffee')

  const products = [
    { value: 'coffee', label: 'Coffee' },
    { value: 'tea', label: 'Tea' },
    { value: 'snacks', label: 'Snacks' },
    { value: 'juice', label: 'Juice' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Forecast</h1>
        <p className="text-gray-600 mt-1">AI-powered sales predictions and insights</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Product Selection</CardTitle>
        </CardHeader>
        <CardContent>
          <Select
            label="Select Product"
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
            options={products}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sales Forecast</CardTitle>
          <CardDescription>Next 5 days prediction with confidence intervals</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="actual" stroke="#2563eb" strokeWidth={2} name="Actual Sales" />
              <Line type="monotone" dataKey="forecast" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" name="Forecast" />
              <Line type="monotone" dataKey="upper" stroke="#d1d5db" strokeWidth={1} strokeDasharray="2 2" name="Upper Bound" />
              <Line type="monotone" dataKey="lower" stroke="#d1d5db" strokeWidth={1} strokeDasharray="2 2" name="Lower Bound" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-gray-600">RMSE</p>
            <h3 className="text-2xl font-bold mt-2">2.45</h3>
            <p className="text-xs text-gray-500 mt-1">Root Mean Square Error</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-gray-600">MAE</p>
            <h3 className="text-2xl font-bold mt-2">1.89</h3>
            <p className="text-xs text-gray-500 mt-1">Mean Absolute Error</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm text-gray-600">MAPE</p>
            <h3 className="text-2xl font-bold mt-2">3.2%</h3>
            <p className="text-xs text-gray-500 mt-1">Mean Absolute Percentage Error</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Key Drivers (SHAP Analysis)</CardTitle>
          <CardDescription>Factors influencing sales forecast</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-2 border-b">
              <span className="font-medium">Day of Week</span>
              <div className="flex items-center">
                <div className="w-32 bg-green-200 h-2 rounded mr-2"></div>
                <span className="text-sm">+8.2%</span>
              </div>
            </div>
            <div className="flex justify-between items-center pb-2 border-b">
              <span className="font-medium">Weather (Sunny)</span>
              <div className="flex items-center">
                <div className="w-24 bg-green-200 h-2 rounded mr-2"></div>
                <span className="text-sm">+5.1%</span>
              </div>
            </div>
            <div className="flex justify-between items-center pb-2 border-b">
              <span className="font-medium">Promotion Active</span>
              <div className="flex items-center">
                <div className="w-40 bg-green-200 h-2 rounded mr-2"></div>
                <span className="text-sm">+12.5%</span>
              </div>
            </div>
            <div className="flex justify-between items-center pb-2 border-b">
              <span className="font-medium">Seasonality</span>
              <div className="flex items-center">
                <div className="w-20 bg-green-200 h-2 rounded mr-2"></div>
                <span className="text-sm">+3.1%</span>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-medium">Competition Pricing</span>
              <div className="flex items-center">
                <div className="w-16 bg-red-200 h-2 rounded mr-2"></div>
                <span className="text-sm text-red-600">-2.3%</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Forecast
