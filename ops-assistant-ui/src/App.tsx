import { useEffect, useRef, useState, type FormEvent } from 'react'
import {
  Alert,
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  IconButton,
  Paper,
  Snackbar,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import AddCommentOutlined from '@mui/icons-material/AddCommentOutlined'
import ArrowUpwardRounded from '@mui/icons-material/ArrowUpwardRounded'
import AutoAwesomeRounded from '@mui/icons-material/AutoAwesomeRounded'
import CheckCircleOutlineRounded from '@mui/icons-material/CheckCircleOutlineRounded'
import CloudOutlined from '@mui/icons-material/CloudOutlined'
import DnsOutlined from '@mui/icons-material/DnsOutlined'
import Inventory2Outlined from '@mui/icons-material/Inventory2Outlined'
import MonitorHeartOutlined from '@mui/icons-material/MonitorHeartOutlined'
import NotificationsActiveRounded from '@mui/icons-material/NotificationsActiveRounded'
import ShieldOutlined from '@mui/icons-material/ShieldOutlined'
import axios from 'axios'

type ChatMessage = { role: 'user' | 'assistant'; content: string }
type ChatResponse = { success: boolean; data: { answer: string } }
type OpsAlert = {
  id: string
  source: string
  severity: 'warning' | 'error' | 'critical'
  title: string
  resource_name: string | null
  scope: string | null
  occurred_at: string | null
  summary: string
}
type AlertChange = { condition: 'fired' | 'resolved'; alert: OpsAlert }
type AlertSnapshot = { alerts: OpsAlert[]; checked_at: string }

const apiBaseUrl = import.meta.env.VITE_ASSISTANT_API_URL?.trim() || '/api/v1'

const suggestions = [
  { label: 'Summarize resources across my subscription', icon: Inventory2Outlined },
  { label: 'Check reported Azure resource health', icon: MonitorHeartOutlined },
  { label: 'Investigate an incident and explain the likely root cause', icon: AutoAwesomeRounded },
  { label: 'Show recent Azure activity from my log workspaces', icon: CloudOutlined },
  { label: 'Check recent AKS events and container logs', icon: DnsOutlined },
]

function boundedHistory(messages: ChatMessage[]): ChatMessage[] {
  const selected: ChatMessage[] = []
  let characters = 0
  for (const message of [...messages].reverse()) {
    if (selected.length === 12 || characters + message.content.length > 12000) break
    selected.push(message)
    characters += message.content.length
  }
  return selected.reverse()
}

function describeError(error: unknown): string {
  if (axios.isAxiosError<{ detail?: string; error?: { message?: string } }>(error)) {
    return error.response?.data?.error?.message ?? error.response?.data?.detail ??
      'The assistant request failed. Check the backend configuration and try again.'
  }
  if (error instanceof Error) return error.message
  return 'The assistant request failed. Please try again.'
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [alerts, setAlerts] = useState<OpsAlert[]>([])
  const [alertError, setAlertError] = useState('')
  const [lastAlertCheck, setLastAlertCheck] = useState('')
  const [alertNotice, setAlertNotice] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const previousAlertIds = useRef(new Set<string>())

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, busy])

  useEffect(() => {
    let active = true
    let controller: AbortController | null = null
    let connecting = false
    let reconnectTimer = 0

    function consumeEvent(eventName: string, data: string) {
      if (eventName === 'snapshot') {
        const snapshot = JSON.parse(data) as AlertSnapshot
        setAlerts(snapshot.alerts)
        previousAlertIds.current = new Set(snapshot.alerts.map((alert) => alert.id))
        setLastAlertCheck(snapshot.checked_at)
        setAlertError('')
        return
      }
      if (eventName !== 'alert') return

      const change = JSON.parse(data) as AlertChange
      const changedAt = new Date().toISOString()
      setLastAlertCheck(changedAt)
      if (change.condition === 'resolved') {
        previousAlertIds.current.delete(change.alert.id)
        setAlerts((current) => current.filter((alert) => alert.id !== change.alert.id))
        setAlertNotice(`Resolved: ${change.alert.title}`)
        return
      }

      const isNew = !previousAlertIds.current.has(change.alert.id)
      previousAlertIds.current.add(change.alert.id)
      setAlerts((current) => [
        change.alert,
        ...current.filter((alert) => alert.id !== change.alert.id),
      ])
      if (isNew) setAlertNotice(`New issue: ${change.alert.title}`)
    }

    async function streamAlerts(signal: AbortSignal) {
      const response = await fetch(
        `${apiBaseUrl.replace(/\/$/, '')}/ops-assistant/alerts/stream`,
        {
          headers: { Accept: 'text/event-stream' },
          signal,
        },
      )
      if (!response.ok) {
        const body = await response.json().catch(() => null) as { detail?: string } | null
        throw new Error(body?.detail ?? 'The live alert feed could not connect.')
      }
      if (!response.body) throw new Error('The live alert stream returned no data.')
      setAlertError('')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      try {
        while (active && !signal.aborted) {
          const { value, done } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          let separator = buffer.indexOf('\n\n')
          while (separator !== -1) {
            const packet = buffer.slice(0, separator)
            buffer = buffer.slice(separator + 2)
            const eventName = packet.match(/^event:\s*(.+)$/m)?.[1]
            const data = packet
              .split(/\r?\n/)
              .filter((line) => line.startsWith('data:'))
              .map((line) => line.slice(5).trim())
              .join('\n')
            if (eventName && data) consumeEvent(eventName, data)
            separator = buffer.indexOf('\n\n')
          }
        }
      } finally {
        reader.releaseLock()
      }
    }

    async function connect() {
      if (connecting || !active || document.visibilityState !== 'visible') return
      connecting = true
      controller = new AbortController()
      const streamController = controller
      try {
        await streamAlerts(streamController.signal)
        if (active && !streamController.signal.aborted) {
          throw new Error('The live alert stream disconnected.')
        }
      } catch (streamError) {
        if (active && !streamController.signal.aborted) {
          setAlertError(describeError(streamError))
        }
      } finally {
        connecting = false
        if (active && document.visibilityState === 'visible') {
          reconnectTimer = window.setTimeout(() => void connect(), 15_000)
        }
      }
    }

    const onVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        controller?.abort()
      } else if (!controller || controller.signal.aborted) {
        void connect()
      }
    }
    if (document.visibilityState === 'visible') void connect()
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => {
      active = false
      controller?.abort()
      window.clearTimeout(reconnectTimer)
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [])

  async function sendMessage(content: string) {
    const text = content.trim()
    if (!text || busy || text.length > 4000) return
    const nextMessages: ChatMessage[] = [...messages, { role: 'user', content: text }]
    setMessages(nextMessages)
    setDraft('')
    setError('')
    setBusy(true)
    try {
      const response = await axios.post<ChatResponse>(
        `${apiBaseUrl.replace(/\/$/, '')}/ops-assistant/chat`,
        { messages: boundedHistory(nextMessages) },
      )
      setMessages((current) => [...current, { role: 'assistant', content: response.data.data.answer }])
    } catch (sendError) {
      setError(describeError(sendError))
    } finally {
      setBusy(false)
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void sendMessage(draft)
  }

  function newConversation() {
    setMessages([])
    setDraft('')
    setError('')
  }

  return (
    <Box className="app-shell">
      <Box component="aside" className="side-rail">
        <Box className="brand-lockup">
          <Box className="brand-mark"><CloudOutlined /></Box>
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="overline" className="eyebrow">EITOAP / CLOUD</Typography>
            <Typography variant="h6" className="brand-title">Ops Assistant</Typography>
          </Box>
        </Box>
        <Tooltip title="Start a new conversation">
          <Button
            aria-label="Start a new conversation"
            onClick={newConversation}
            className="new-chat"
            startIcon={<AddCommentOutlined />}
          >
            New conversation
          </Button>
        </Tooltip>
        <Box className="nav-section">
          <Typography variant="overline" className="nav-label">WORKSPACE</Typography>
          <Box className="nav-item active">
            <AutoAwesomeRounded />
            <Typography variant="body2">AI Assistant</Typography>
            <Box className="nav-active-dot" />
          </Box>
        </Box>
        <Paper elevation={0} className="scope-card">
          <Stack direction="row" alignItems="center" spacing={1}>
            <Box className="scope-icon"><DnsOutlined /></Box>
            <Typography variant="overline" className="scope-kicker">ACCESS SCOPE</Typography>
          </Stack>
          <Typography variant="body2" className="scope-title">Azure subscription</Typography>
          <Typography variant="caption" color="text.secondary">Inventory · health · metrics · logs</Typography>
          <Chip
            size="small"
            icon={<CheckCircleOutlineRounded />}
            label="Read-only access"
            className="scope-chip"
          />
        </Paper>
        <Box className="rail-spacer" />
        <Box className="security-note">
          <ShieldOutlined fontSize="small" />
          <Box>
            <Typography variant="caption" display="block">Public demo access</Typography>
            <Typography variant="caption" color="text.secondary">Treat Azure results as public</Typography>
          </Box>
        </Box>
      </Box>

      <Box component="main" className="main-panel">
        <Box component="header" className="topbar">
          <Stack direction="row" alignItems="center" spacing={1.25}>
            <Box className="status-dot" />
            <Typography variant="body2" color="text.secondary">
              Operations workspace <Box component="span" className="topbar-separator">/</Box> Read-only diagnostics
            </Typography>
          </Stack>
          <Chip size="small" label="Public demo" />
        </Box>

        <Box className="conversation">
          <Paper elevation={0} className="alert-center">
              <Stack direction="row" alignItems="center" spacing={1.25} className="alert-center-heading">
                <Box className="alert-center-icon"><NotificationsActiveRounded /></Box>
                <Box className="alert-center-copy">
                  <Typography variant="subtitle2">Live monitoring</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Azure Monitor events stream while this tab is open
                  </Typography>
                </Box>
                <Chip
                  size="small"
                  label={`${alerts.length} active`}
                  className={alerts.length ? 'alert-count active' : 'alert-count'}
                />
                {lastAlertCheck && (
                  <Typography variant="caption" className="last-alert-check">
                    Updated {new Date(lastAlertCheck).toLocaleTimeString()}
                  </Typography>
                )}
              </Stack>
              {alertError && <Alert severity="error" className="alert-source-warning">{alertError}</Alert>}
              {alerts.length > 0 ? (
                <Stack spacing={1} className="active-alert-list">
                  {alerts.slice(0, 5).map((alert) => (
                    <Box key={alert.id} className={`active-alert ${alert.severity}`}>
                      <Box className="active-alert-marker" />
                      <Box className="active-alert-content">
                        <Typography variant="body2" className="active-alert-title">
                          {alert.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {[alert.resource_name, alert.scope, alert.source]
                            .filter(Boolean)
                            .join(' · ')}
                          {alert.occurred_at && ` · ${new Date(alert.occurred_at).toLocaleTimeString()}`}
                        </Typography>
                        <Typography variant="caption" display="block" className="active-alert-summary">
                          {alert.summary}
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                  {alerts.length > 5 && (
                    <Typography variant="caption" color="text.secondary" className="more-alerts">
                      And {alerts.length - 5} more active alert{alerts.length - 5 === 1 ? '' : 's'}
                    </Typography>
                  )}
                </Stack>
              ) : (
                <Typography variant="body2" className="no-alert-signals">
                  {alertError
                    ? 'The live monitoring stream needs attention; review its status above.'
                    : 'No active Azure Monitor alerts.'}
                </Typography>
              )}
          </Paper>
          {messages.length === 0 ? (
            <Box className="welcome">
              <Box className="welcome-orb"><AutoAwesomeRounded /></Box>
              <Typography variant="overline" className="eyebrow">YOUR AZURE OPERATIONS COPILOT</Typography>
              <Typography variant="h3" className="welcome-title">Clarity for your<br />cloud operations.</Typography>
              <Typography color="text.secondary" className="welcome-copy">
                Ask in plain language. I can inspect resources across the configured subscription,
                check reported health and metrics, and search approved tables in every Log Analytics
                workspace in the subscription.
              </Typography>
              <Stack direction="row" spacing={1} className="welcome-badges">
                <Chip size="small" icon={<ShieldOutlined />} label="Public demo" />
                <Chip size="small" icon={<CheckCircleOutlineRounded />} label="Read-only tools" />
                <Chip size="small" icon={<CloudOutlined />} label="Azure + AKS" />
              </Stack>
              <Typography variant="overline" className="suggestion-heading">GET STARTED</Typography>
              <Box className="suggestion-grid">
                {suggestions.map(({ label, icon: Icon }) => (
                  <Button
                    key={label}
                    variant="outlined"
                    className="suggestion"
                    startIcon={<Icon />}
                    onClick={() => void sendMessage(label)}
                    disabled={busy}
                  >
                    {label}
                  </Button>
                ))}
              </Box>
            </Box>
          ) : (
            <Stack className="message-list" spacing={2.5}>
              {messages.map((message, index) => (
                <Box
                  key={`${message.role}-${index}`}
                  className={`message-row ${message.role === 'user' ? 'from-user' : 'from-agent'}`}
                >
                  {message.role === 'assistant' && <Avatar className="message-avatar"><CloudOutlined /></Avatar>}
                  <Paper elevation={0} className={`message-bubble ${message.role}`}>
                    <Typography component="div" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>
                      {message.content}
                    </Typography>
                  </Paper>
                </Box>
              ))}
              {busy && (
                <Stack direction="row" alignItems="center" spacing={1.5} className="thinking">
                  <CircularProgress size={18} />
                  <Typography variant="body2" color="text.secondary">Checking Azure with read-only tools…</Typography>
                </Stack>
              )}
              <div ref={bottomRef} />
            </Stack>
          )}
        </Box>

        <Box className="composer-wrap">
          {error && <Alert severity="error" sx={{ mb: 1.5 }}>{error}</Alert>}
          <Paper component="form" elevation={0} onSubmit={submit} className="composer">
            <TextField
              fullWidth
              multiline
              maxRows={5}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about resources, health, metrics, activity, or AKS logs…"
              inputProps={{ maxLength: 4000, 'aria-label': 'Ask the operations assistant' }}
              disabled={busy}
              variant="standard"
              InputProps={{ disableUnderline: true }}
            />
            <Tooltip title="Send message">
              <span>
                <IconButton
                  type="submit"
                  color="primary"
                  aria-label="Send message"
                  disabled={!draft.trim() || busy || draft.length > 4000}
                  className="send-button"
                >
                  <ArrowUpwardRounded />
                </IconButton>
              </span>
            </Tooltip>
            <Typography variant="caption" color="text.secondary" className="composer-hint">
              Public demo: don’t enter secrets or sensitive data.
            </Typography>
          </Paper>
          <Divider sx={{ mt: 2, mb: 1.5, borderColor: 'rgba(255,255,255,.08)' }} />
          <Typography variant="caption" color="text.secondary" className="disclaimer">
            AI responses can be inaccurate. Diagnostics are read-only; review recommendations before acting.
          </Typography>
        </Box>
      </Box>
      <Snackbar
        open={Boolean(alertNotice)}
        autoHideDuration={6000}
        onClose={() => setAlertNotice('')}
        message={alertNotice}
      />
    </Box>
  )
}
