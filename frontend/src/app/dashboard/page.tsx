'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { DollarSign, ShoppingCart, Package, AlertTriangle, Sparkles } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/format'
import { MetricsResponse, Recommendation } from '@/types'
import StatCard from '@/components/ui/StatCard'
import Badge, { statusToVariant } from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isTriggering, setIsTriggering] = useState(false)
  const [error, setError] = useState('')

  const loadData = async () => {
    try {
      const [metricsData, recsData] = await Promise.all([
        apiClient.getMetrics(30),
        apiClient.getRecommendations(5),
      ])
      setMetrics(metricsData)
      setRecommendations(recsData)
    } catch (err) {
      setError('Failed to load dashboard data')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleTriggerWorkflow = async () => {
    setIsTriggering(true)
    try {
      await apiClient.triggerWorkflow()
      await loadData()
    } catch (err) {
      setError('Failed to trigger workflow')
    } finally {
      setIsTriggering(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div>
      <div className="header-main">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-1">Overview of your operations, last {metrics?.period_days ?? 30} days</p>
        </div>
        <Button onClick={handleTriggerWorkflow} isLoading={isTriggering}>
          <Sparkles className="w-4 h-4" />
          Run AI Workflow
        </Button>
      </div>

      {error && (
        <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard label="Total Sales" value={formatCurrency(metrics?.sales.total_sales ?? 0)} icon={DollarSign} accent="success" />
        <StatCard label="Orders" value={metrics?.sales.order_count ?? 0} icon={ShoppingCart} accent="primary" />
        <StatCard label="Total Products" value={metrics?.inventory.total_products ?? 0} icon={Package} accent="primary" />
        <StatCard label="Low Stock Items" value={metrics?.inventory.low_stock_items ?? 0} icon={AlertTriangle} accent="warning" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="px-6 py-4 border-b border-slate-200">
            <h2 className="font-semibold text-slate-900">Top Products</h2>
          </div>
          {metrics && metrics.top_products.length > 0 ? (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Name</th>
                    <th>Price</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.top_products.map((p) => (
                    <tr key={p.id}>
                      <td className="text-slate-500">{p.sku}</td>
                      <td className="font-medium">{p.name}</td>
                      <td>{formatCurrency(p.price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState title="No product data yet" description="Top products will appear once orders come in" />
          )}
        </div>

        <div className="card">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
            <h2 className="font-semibold text-slate-900">Recent Recommendations</h2>
            <Link href="/dashboard/recommendations" className="link-primary text-sm">
              View all
            </Link>
          </div>
          {recommendations.length > 0 ? (
            <ul className="divide-y divide-slate-200">
              {recommendations.map((rec) => (
                <li key={rec.id} className="px-6 py-4">
                  <div className="flex items-start justify-between gap-4">
                    <p className="text-sm text-slate-900 font-medium">{rec.executive_summary}</p>
                    <Badge variant={statusToVariant(rec.approval_status)}>{rec.approval_status}</Badge>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{formatDate(rec.created_at, 'MMM d, yyyy · h:mm a')}</p>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              icon={Sparkles}
              title="No recommendations yet"
              description="Run the AI workflow to generate your first recommendations"
            />
          )}
        </div>
      </div>
    </div>
  )
}
