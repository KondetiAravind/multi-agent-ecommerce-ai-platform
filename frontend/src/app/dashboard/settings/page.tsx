'use client'

import { useState } from 'react'
import { CheckCircle2, XCircle, LogOut } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import Button from '@/components/ui/Button'

export default function SettingsPage() {
  const { user, logout } = useAuth()
  const [isChecking, setIsChecking] = useState(false)
  const [status, setStatus] = useState<'idle' | 'ok' | 'error'> ('idle')
  const [info, setInfo] = useState<{ name: string; version: string; description: string } | null>(null)

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
  const appName = process.env.NEXT_PUBLIC_APP_NAME || 'E-commerce AI Operations'
  const appVersion = process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'

  const testConnection = async () => {
    setIsChecking(true)
    setStatus('idle')
    try {
      await apiClient.getHealth()
      const infoData = await apiClient.getInfo()
      setInfo(infoData)
      setStatus('ok')
    } catch {
      setStatus('error')
      setInfo(null)
    } finally {
      setIsChecking(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <div className="header-main">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
          <p className="text-slate-500 text-sm mt-1">Account and connection details</p>
        </div>
      </div>

      <div className="card p-6 mb-6">
        <h2 className="font-semibold text-slate-900 mb-4">Account</h2>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-500">Email</span>
            <span className="font-medium text-slate-900">{user?.email}</span>
          </div>
        </div>
        <div className="mt-6">
          <Button variant="secondary" onClick={logout}>
            <LogOut className="w-4 h-4" />
            Log out
          </Button>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="font-semibold text-slate-900 mb-4">Application</h2>
        <div className="space-y-3 text-sm mb-6">
          <div className="flex justify-between">
            <span className="text-slate-500">App Name</span>
            <span className="font-medium text-slate-900">{appName}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Frontend Version</span>
            <span className="font-medium text-slate-900">{appVersion}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">API Base URL</span>
            <span className="font-medium text-slate-900">{apiBaseUrl}</span>
          </div>
          {info && (
            <>
              <div className="flex justify-between">
                <span className="text-slate-500">Backend Service</span>
                <span className="font-medium text-slate-900">{info.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Backend Version</span>
                <span className="font-medium text-slate-900">{info.version}</span>
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-4">
          <Button variant="secondary" onClick={testConnection} isLoading={isChecking}>
            Test Connection
          </Button>
          {status === 'ok' && (
            <span className="flex items-center gap-1.5 text-sm text-green-600 font-medium">
              <CheckCircle2 className="w-4 h-4" />
              Connected
            </span>
          )}
          {status === 'error' && (
            <span className="flex items-center gap-1.5 text-sm text-red-600 font-medium">
              <XCircle className="w-4 h-4" />
              Unable to reach backend
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
