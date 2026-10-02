import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import {
  Alert,
  Avatar,
  Box,
  Button,
  CircularProgress,
  Divider,
  IconButton,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import AddCommentOutlined from '@mui/icons-material/AddCommentOutlined'
import ArrowUpwardRounded from '@mui/icons-material/ArrowUpwardRounded'
import CloudOutlined from '@mui/icons-material/CloudOutlined'
import Inventory2Outlined from '@mui/icons-material/Inventory2Outlined'
import MonitorHeartOutlined from '@mui/icons-material/MonitorHeartOutlined'
import ShieldOutlined from '@mui/icons-material/ShieldOutlined'
import { InteractionRequiredAuthError, PublicClientApplication, type AccountInfo } from '@azure/msal-browser'
import axios from 'axios'

type ChatMessage = { role: 'user' | 'assistant'; content: string }
type ChatResponse = { success: boolean; data: { answer: string } }

const apiScope = import.meta.env.VITE_ASSISTANT_API_SCOPE?.trim() ?? ''
const apiBaseUrl = import.meta.env.VITE_ASSISTANT_API_URL?.trim() || '/api/v1'
const msalInstance = new PublicClientApplication({
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID ?? '',
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID ?? 'common'}`,
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: { cacheLocation: 'sessionStorage', storeAuthStateInCookie: false },
})

const suggestions = [
  { label: 'Check reported Azure resource health', icon: MonitorHeartOutlined },
  { label: 'List the resources in my monitored resource groups', icon: Inventory2Outlined },
  { label: 'Explain how this project deploys to AKS', icon: CloudOutlined },
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
  const [account, setAccount] = useState<AccountInfo | null>(null)
  const [authReady, setAuthReady] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const setupError = useMemo(() => {
    if (!import.meta.env.VITE_ENTRA_CLIENT_ID) return 'Set VITE_ENTRA_CLIENT_ID to enable sign-in.'
    if (!apiScope) return 'Set VITE_ASSISTANT_API_SCOPE to the Entra scope exposed by the backend API.'
    return ''
  }, [])

  useEffect(() => {
    let active = true
    void (async () => {
      try {
        await msalInstance.initialize()
        const redirectResult = await msalInstance.handleRedirectPromise()
        const signedInAccount =
          redirectResult?.account ??
          msalInstance.getActiveAccount() ??
          msalInstance.getAllAccounts()[0] ??
          null
        if (signedInAccount) msalInstance.setActiveAccount(signedInAccount)
        if (active) {
          setAccount(signedInAccount)
          setAuthReady(true)
        }
      } catch {
        if (active) {
          setError('Microsoft Entra sign-in could not be initialized. Check the client and redirect URI configuration.')
          setAuthReady(true)
        }
      }
    })()
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, busy])

  async function signIn() {
    if (setupError) return
    await msalInstance.loginRedirect({ scopes: [apiScope] })
  }

  async function getAccessToken(): Promise<string> {
    if (!account) throw new Error('Sign in with your work account to continue.')
    try {
      const result = await msalInstance.acquireTokenSilent({ scopes: [apiScope], account })
      return result.accessToken
    } catch (tokenError) {
      if (tokenError instanceof InteractionRequiredAuthError) {
        await msalInstance.acquireTokenRedirect({ scopes: [apiScope], account })
      }
      throw tokenError
    }
  }

  async function sendMessage(content: string) {
    const text = content.trim()
    if (!text || busy || text.length > 4000) return
    const nextMessages: ChatMessage[] = [...messages, { role: 'user', content: text }]
    setMessages(nextMessages)
    setDraft('')
    setError('')
    setBusy(true)
    try {
      const token = await getAccessToken()
      const response = await axios.post<ChatResponse>(
        `${apiBaseUrl.replace(/\/$/, '')}/ops-assistant/chat`,
        { messages: boundedHistory(nextMessages).filter((message) => message.role === 'user') },
        { headers: { Authorization: `Bearer ${token}` } },
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

  const signedInLabel = account?.name ?? account?.username

  return (
    <Box className="app-shell">
      <Box component="aside" className="side-rail">
        <Box className="brand-mark"><CloudOutlined /></Box>
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="overline" className="eyebrow">EITOAP / CLOUD</Typography>
          <Typography variant="h6" className="brand-title">Ops Assistant</Typography>
        </Box>
        <Tooltip title="Start a new conversation">
          <IconButton aria-label="Start a new conversation" onClick={newConversation} className="new-chat">
            <AddCommentOutlined />
          </IconButton>
        </Tooltip>
        <Box className="rail-spacer" />
        <Box className="security-note">
          <ShieldOutlined fontSize="small" />
          <Typography variant="caption">Entra protected</Typography>
        </Box>
      </Box>

      <Box component="main" className="main-panel">
        <Box component="header" className="topbar">
          <Stack direction="row" alignItems="center" spacing={1.25}>
            <Box className="status-dot" />
            <Typography variant="body2" color="text.secondary">
              Azure operations · Read-only diagnostics
            </Typography>
          </Stack>
          <Typography variant="body2" className="account-label">
            {signedInLabel || 'Not signed in'}
          </Typography>
        </Box>

        <Box className="conversation">
          {messages.length === 0 ? (
            <Box className="welcome">
              <Avatar className="welcome-avatar"><CloudOutlined /></Avatar>
              <Typography variant="overline" className="eyebrow">AZURE OPERATIONS</Typography>
              <Typography variant="h3" className="welcome-title">How can I help<br />with your deployment?</Typography>
              <Typography color="text.secondary" className="welcome-copy">
                Ask about the EITOAP deployment, or request a read-only check of the Azure resources
                in its configured resource groups.
              </Typography>
              <Box className="suggestion-grid">
                {suggestions.map(({ label, icon: Icon }) => (
                  <Button
                    key={label}
                    variant="outlined"
                    className="suggestion"
                    startIcon={<Icon />}
                    onClick={() => void sendMessage(label)}
                    disabled={!account || busy}
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
                  <Typography variant="body2" color="text.secondary">Checking your request…</Typography>
                </Stack>
              )}
              <div ref={bottomRef} />
            </Stack>
          )}
        </Box>

        <Box className="composer-wrap">
          {setupError && <Alert severity="warning" sx={{ mb: 1.5 }}>{setupError}</Alert>}
          {error && <Alert severity="error" sx={{ mb: 1.5 }}>{error}</Alert>}
          {!account ? (
            <Button
              variant="contained"
              onClick={() => void signIn()}
              disabled={!authReady || Boolean(setupError)}
              sx={{ minHeight: 48, px: 3 }}
            >
              {authReady ? 'Sign in with Microsoft Entra ID' : <CircularProgress size={20} />}
            </Button>
          ) : (
            <Paper component="form" elevation={0} onSubmit={submit} className="composer">
              <TextField
                fullWidth
                multiline
                maxRows={5}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Ask about your Azure or AKS deployment…"
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
                Don’t include passwords, tokens, or other secrets.
              </Typography>
            </Paper>
          )}
          <Divider sx={{ mt: 2, mb: 1.5, borderColor: 'rgba(255,255,255,.08)' }} />
          <Typography variant="caption" color="text.secondary" className="disclaimer">
            AI responses can be inaccurate. Diagnostics are read-only; review recommendations before acting.
          </Typography>
        </Box>
      </Box>
    </Box>
  )
}
