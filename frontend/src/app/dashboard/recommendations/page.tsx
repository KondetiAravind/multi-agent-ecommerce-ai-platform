'use client'

import { useEffect, useState } from 'react'
import { Sparkles, Check, X as XIcon, TrendingUp, Package, Tag, Lightbulb } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { formatDate, formatPercent } from '@/lib/format'
import { AIPerformance, Recommendation } from '@/types'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import Badge, { statusToVariant } from '@/components/ui/Badge'

const STATUS_TABS = ['all', 'pending', 'approved', 'rejected']

const AI_OPS = [
  { key: 'forecast', label: 'Demand Forecast', icon: TrendingUp, run: () => apiClient.runDemandForecast() },
  { key: 'inventory', label: 'Inventory Optimization', icon: Package, run: () => apiClient.runInventoryOptimization() },
  { key: 'pricing', label: 'Pricing Optimization', icon: Tag, run: () => apiClient.runPricingOptimization() },
] as const

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [statusFilter, setStatusFilter] = useState('all')
  const [performance, setPerformance] = useState<AIPerformance | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isTriggering, setIsTriggering] = useState(false)
  const [actioningId, setActioningId] = useState<number | null>(null)

  const [runningOp, setRunningOp] = useState<string | null>(null)
  const [opResult, setOpResult] = useState<{ label: string; data: any } | null>(null)

  const loadData = async (status = statusFilter) => {
    setIsLoading(true)
    setError('')
    try {
      const [recs, perf] = await Promise.all([
        apiClient.getRecommendations(50, status === 'all' ? undefined : status),
        apiClient.getAIPerformance(),
      ])
      setRecommendations(recs)
      setPerformance(perf)
    } catch {
      setError('Failed to load recommendations')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleFilterChange = (status: string) => {
    setStatusFilter(status)
    loadData(status)
  }

  const handleTriggerWorkflow = async () => {
    setIsTriggering(true)
    setError('')
    try {
      await apiClient.triggerWorkflow()
      await loadData()
    } catch {
      setError('Failed to trigger workflow')
    } finally {
      setIsTriggering(false)
    }
  }

  const handleDecision = async (id: number, decision: 'approve' | 'reject') => {
    setActioningId(id)
    setError('')
    try {
      if (decision === 'approve') await apiClient.approveRecommendation(id)
      else await apiClient.rejectRecommendation(id)
      setRecommendations((prev) =>
        prev.map((r) => (r.id === id ? { ...r, approval_status: decision === 'approve' ? 'approved' : 'rejected' } : r))
      )
    } catch {
      setError('Failed to update recommendation')
    } finally {
      setActioningId(null)
    }
  }

  const handleRunOp = async (op: (typeof AI_OPS)[number]) => {
    setRunningOp(op.key)
    setError('')
    try {
      const data = await op.run()
      setOpResult({ label: op.label, data })
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to run ${op.label}`)
    } finally {
      setRunningOp(null)
    }
  }

  return (
    <div>
      <div className="header-main">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Recommendations</h1>
          <p className="text-slate-500 text-sm mt-1">AI-generated operational recommendations</p>
        </div>
        <Button onClick={handleTriggerWorkflow} isLoading={isTriggering}>
          <Sparkles className="w-4 h-4" />
          Run AI Workflow
        </Button>
      </div>

      {error && (
        <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      {performance && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-8">
          <div className="card p-4 text-center">
            <p className="text-xl font-bold text-slate-900">{performance.total}</p>
            <p className="text-xs text-slate-500">Total</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-xl font-bold text-slate-900">{formatPercent(performance.average_confidence)}</p>
            <p className="text-xs text-slate-500">Avg Confidence</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-xl font-bold text-green-600">{performance.approved}</p>
            <p className="text-xs text-slate-500">Approved</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-xl font-bold text-red-600">{performance.rejected}</p>
            <p className="text-xs text-slate-500">Rejected</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-xl font-bold text-yellow-600">{performance.pending}</p>
            <p className="text-xs text-slate-500">Pending</p>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex gap-2">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => handleFilterChange(tab)}
              className={`btn ${statusFilter === tab ? 'btn-primary' : 'btn-secondary'} capitalize`}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {AI_OPS.map((op) => (
            <Button
              key={op.key}
              variant="secondary"
              onClick={() => handleRunOp(op)}
              isLoading={runningOp === op.key}
            >
              <op.icon className="w-4 h-4" />
              {op.label}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : recommendations.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={Lightbulb}
            title="No recommendations found"
            description="Run the AI workflow to generate recommendations"
          />
        </div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <div key={rec.id} className="card p-6">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <p className="font-semibold text-slate-900">{rec.executive_summary}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {formatDate(rec.created_at, 'MMM d, yyyy · h:mm a')} · Confidence {formatPercent(rec.confidence_score)}
                  </p>
                </div>
                <Badge variant={statusToVariant(rec.approval_status)}>{rec.approval_status}</Badge>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm mb-4">
                {rec.reasoning.high_demand && (
                  <div className="bg-slate-50 rounded-lg p-3">
                    <p className="font-medium text-slate-700 mb-1">Demand</p>
                    <p className="text-slate-600">{rec.reasoning.high_demand}</p>
                  </div>
                )}
                {rec.reasoning.low_inventory && (
                  <div className="bg-slate-50 rounded-lg p-3">
                    <p className="font-medium text-slate-700 mb-1">Inventory</p>
                    <p className="text-slate-600">{rec.reasoning.low_inventory}</p>
                  </div>
                )}
                {rec.reasoning.market_trend && (
                  <div className="bg-slate-50 rounded-lg p-3">
                    <p className="font-medium text-slate-700 mb-1">Market Trend</p>
                    <p className="text-slate-600">{rec.reasoning.market_trend}</p>
                  </div>
                )}
                {rec.reasoning.revenue_impact && (
                  <div className="bg-slate-50 rounded-lg p-3">
                    <p className="font-medium text-slate-700 mb-1">Revenue Impact</p>
                    <p className="text-slate-600">{rec.reasoning.revenue_impact}</p>
                  </div>
                )}
              </div>

              {rec.approval_status === 'pending' && (
                <div className="flex gap-3">
                  <Button variant="success" onClick={() => handleDecision(rec.id, 'approve')} isLoading={actioningId === rec.id}>
                    <Check className="w-4 h-4" />
                    Approve
                  </Button>
                  <Button variant="danger" onClick={() => handleDecision(rec.id, 'reject')} isLoading={actioningId === rec.id}>
                    <XIcon className="w-4 h-4" />
                    Reject
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {opResult && (
        <Modal title={opResult.label} onClose={() => setOpResult(null)} maxWidth="max-w-lg">
          <pre className="bg-slate-50 rounded-lg p-4 text-xs overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(opResult.data, null, 2)}
          </pre>
        </Modal>
      )}
    </div>
  )
}
