import { 
  Box, 
  Grid, 
  Typography, 
  Stack, 
  Card, 
  Drawer, 
  IconButton, 
  TextField, 
  Avatar, 
  Chip, 
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  CircularProgress
} from '@mui/material'
import {
  LockRounded,
  HistoryRounded,
  NotificationsRounded,
  PersonRounded,
  SecurityRounded,
  VpnLockRounded,
  AppShortcutRounded,
  SearchRounded,
  CloseRounded,
  SendRounded,
  SmartToyRounded,
  ArrowForwardRounded
} from '@mui/icons-material'
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../../contexts/AuthContext'
import { Header } from '../../components/Header'

interface ChatMessage {
  sender: 'bot' | 'user'
  text: string
  links?: Array<{ label: string; url: string; isExternal?: boolean }>
}

interface ActivityItem {
  id: number
  timestamp: string
  action: string
  status: string
  ip_address: string | null
  details: Record<string, unknown>
}

interface NotificationItem {
  id: string
  title: string
  message: string
  severity: 'success' | 'warning' | 'info' | 'error'
  timestamp: string
}

export function Dashboard() {
  const navigate = useNavigate()
  const { getAccessToken, user } = useAuth()
  const chatEndRef = useRef<HTMLDivElement>(null)

  // API Data States
  const [stats, setStats] = useState({
    total_requests: 0,
    successful_resets: 0,
    failed_resets: 0,
    pending_approvals: 0,
    active_sessions: 1,
  })
  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [loadingData, setLoadingData] = useState(true)

  // Dialog & Drawer States
  const [copilotOpen, setCopilotOpen] = useState(false)

  // Copilot Chat States
  const [messages, setMessages] = useState<ChatMessage[]>([
    { 
      sender: 'bot', 
      text: 'Hi there! I am your Enterprise IT Assistant. How can I help you today?' 
    }
  ])
  const [inputVal, setInputVal] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  // Fetch Dashboard data on load
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoadingData(true)
      const token = await getAccessToken()
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const apiBase = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

      try {
        const [statsRes, activityRes, notifyRes] = await Promise.all([
          axios.get(`${apiBase}/dashboard/summary`, { headers }),
          axios.get(`${apiBase}/dashboard/recent-activity`, { headers }),
          axios.get(`${apiBase}/dashboard/notifications`, { headers })
        ])

        if (statsRes.data?.success) setStats(statsRes.data.data)
        if (activityRes.data?.success) setActivities(activityRes.data.data)
        if (notifyRes.data?.success) setNotifications(notifyRes.data.data)
      } catch (err) {
        console.error('Failed to load dashboard data', err)
      } finally {
        setLoadingData(false)
      }
    }
    fetchDashboardData()
  }, [getAccessToken])

  const handleSendMockMessage = (text: string) => {
    if (!text.trim()) return
    setMessages((prev) => [...prev, { sender: 'user', text }])
    setInputVal('')
    setIsTyping(true)

    // Simulate smart bot response
    setTimeout(() => {
      setIsTyping(false)
      let replyText = "I'm processing your request. For general issues, you can submit a support ticket or request software. How else can I help?"
      let links: ChatMessage['links'] = []

      const query = text.toLowerCase()
      if (query.includes('password') || query.includes('reset')) {
        replyText = 'You can reset your password securely via our Self-Service Password Reset page.'
        links = [{ label: 'Go to Reset Password', url: '/dashboard/password-reset' }]
      } else if (query.includes('mfa') || query.includes('factor') || query.includes('auth')) {
        replyText = 'You can configure and register your MFA devices securely.'
        links = [{ label: 'Go to MFA Management', url: '/dashboard/mfa-management' }]
      } else if (query.includes('unlock')) {
        replyText = 'If your account is locked due to too many failed attempts, use our self-service unlock tool.'
        links = [{ label: 'Unlock Account Portal', url: '/dashboard/unlock-account' }]
      } else if (query.includes('software') || query.includes('request')) {
        replyText = 'You can request software licenses and automatic installations from our catalog.'
        links = [{ label: 'Request Software', url: '/dashboard/software-request' }]
      } else if (query.includes('vpn') || query.includes('network')) {
        replyText = 'VPN requests are currently scheduled. Note: VPN Self-Service tools are coming soon!'
        links = [{ label: 'VPN Request (Placeholder)', url: '/dashboard/vpn-request' }]
      }

      setMessages((prev) => [...prev, { sender: 'bot', text: replyText, links }])
    }, 1000)
  }

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMockMessage(suggestion)
  }

  const copilotStudioUrl = import.meta.env.VITE_COPILOT_STUDIO_URL || ''

  return (
    <Box>
      <Header
        title="Operations Dashboard"
        subtitle="Welcome to your corporate self-service automation console."
      />

      {/* Hero Welcome Section */}
      <Stack spacing={2} sx={{ alignItems: 'center', textAlign: 'center', mt: 3, mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800, color: 'text.primary', letterSpacing: -0.5 }}>
          How can we help you today, {user?.name}?
        </Typography>

        {/* Copilot Search Bar Trigger */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            width: '100%',
            maxHeight: 52,
            maxWidth: 600,
            px: 2.5,
            py: 1.5,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 8,
            boxShadow: '0 4px 12px rgba(0,0,0,0.03)',
            cursor: 'pointer',
            bgcolor: 'common.white',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              boxShadow: '0 8px 24px rgba(21, 95, 193, 0.1)',
              borderColor: 'primary.main',
            }
          }}
          onClick={() => setCopilotOpen(true)}
        >
          <SearchRounded sx={{ color: 'text.secondary', mr: 2, fontSize: 24 }} />
          <Typography color="text.secondary" sx={{ flexGrow: 1, userSelect: 'none', textAlign: 'left', fontSize: '0.9rem' }}>
            Ask Copilot for IT assistance or search services...
          </Typography>
          <Chip 
            label="Copilot Studio" 
            size="small" 
            color="primary" 
            sx={{ fontWeight: 700, cursor: 'pointer', borderRadius: 2 }} 
          />
        </Box>
      </Stack>

      {/* Notifications Alert Center */}
      {notifications.length > 0 && (
        <Stack spacing={1.5} sx={{ mb: 4, maxWidth: 1200, mx: 'auto' }}>
          {notifications.map((n) => (
            <Alert 
              key={n.id} 
              severity={n.severity} 
              sx={{ borderRadius: 3, border: '1px solid', borderColor: `${n.severity}.light` }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{n.title}</Typography>
              <Typography variant="body2">{n.message}</Typography>
            </Alert>
          ))}
        </Stack>
      )}

      {/* Statistics widgets */}
      {loadingData ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3} sx={{ mb: 4, maxWidth: 1200, mx: 'auto' }}>
          {[
            { label: 'Total Requests', val: stats.total_requests, color: 'primary.main' },
            { label: 'Successful Resets', val: stats.successful_resets, color: 'success.main' },
            { label: 'Failed Resets', val: stats.failed_resets, color: 'error.main' },
            { label: 'Pending Approvals', val: stats.pending_approvals, color: 'warning.main' },
            { label: 'Active Sessions', val: stats.active_sessions, color: 'info.main' },
          ].map((stat) => (
            <Grid key={stat.label} size={{ xs: 12, sm: 6, md: 2.4 }}>
              <Card sx={{ p: 2.5, borderRadius: 4, border: '1px solid', borderColor: 'divider', textAlign: 'center', boxShadow: 'none' }}>
                <Typography variant="h4" sx={{ fontWeight: 800, color: stat.color, mb: 0.5 }}>
                  {stat.val}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700, textTransform: 'uppercase' }}>
                  {stat.label}
                </Typography>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Shortcut Cards Section */}
      <Typography variant="h6" sx={{ fontWeight: 800, mb: 2, maxWidth: 1200, mx: 'auto' }}>
        Core Shortcuts
      </Typography>
      <Grid container spacing={3} sx={{ mb: 5, maxWidth: 1200, mx: 'auto' }}>
        {[
          { label: 'Reset Password', path: '/dashboard/password-reset', icon: LockRounded, color: '#e8f0fe', iconColor: '#1a73e8' },
          { label: 'Reset History', path: '/dashboard/reset-history', icon: HistoryRounded, color: '#e6f4ea', iconColor: '#137333' },
          { label: 'Notifications', path: '/dashboard/notifications', icon: NotificationsRounded, color: '#fef7e0', iconColor: '#b06000' },
          { label: 'My Profile', path: '/dashboard/profile', icon: PersonRounded, color: '#fce8e6', iconColor: '#c5221f' },
        ].map((shortcut) => (
          <Grid key={shortcut.label} size={{ xs: 12, sm: 6, md: 3 }}>
            <Card
              onClick={() => navigate(shortcut.path)}
              sx={{
                p: 3,
                cursor: 'pointer',
                borderRadius: 4,
                border: '1px solid',
                borderColor: 'divider',
                boxShadow: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.04)',
                  borderColor: 'primary.main',
                }
              }}
            >
              <Stack direction="row" spacing={2} alignItems="center">
                <Box sx={{ width: 44, height: 44, borderRadius: 2.5, bgcolor: shortcut.color, color: shortcut.iconColor, display: 'grid', placeItems: 'center' }}>
                  <shortcut.icon />
                </Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                  {shortcut.label}
                </Typography>
              </Stack>
              <ArrowForwardRounded sx={{ color: 'text.secondary', fontSize: 18 }} />
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Service Catalog / Placeholders Section */}
      <Typography variant="h6" sx={{ fontWeight: 800, mb: 2, maxWidth: 1200, mx: 'auto' }}>
        Requests & Access Services
      </Typography>
      <Grid container spacing={3} sx={{ mb: 5, maxWidth: 1200, mx: 'auto' }}>
        {[
          { label: 'Software Request', path: '/dashboard/software-request', icon: AppShortcutRounded, desc: 'Request pre-approved corporate software licenses.' },
          { label: 'VPN Request', path: '/dashboard/vpn-request', icon: VpnLockRounded, desc: 'Submit and provision virtual private network keys.' },
          { label: 'Shared Mailbox', path: '/dashboard/mailbox-request', icon: AppShortcutRounded, desc: 'Request access or setup shared email lists.' },
          { label: 'Access Requests', path: '/dashboard/access-request', icon: VpnLockRounded, desc: 'Request elevated directories and security keys.' },
          { label: 'MFA Management', path: '/dashboard/mfa-management', icon: SecurityRounded, desc: 'Configure and audit multi-factor authentication methods.' },
        ].map((srv) => (
          <Grid key={srv.label} size={{ xs: 12, sm: 6, md: 2.4 }}>
            <Card
              onClick={() => navigate(srv.path)}
              sx={{
                p: 3,
                cursor: 'pointer',
                borderRadius: 4,
                border: '1px solid',
                borderColor: 'divider',
                boxShadow: 'none',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.04)',
                  borderColor: 'primary.main',
                }
              }}
            >
              <Box>
                <Stack direction="row" justifyItems="space-between" alignItems="center" sx={{ mb: 1.5 }}>
                  <Box sx={{ width: 38, height: 38, borderRadius: 2, bgcolor: '#f4f6fb', color: 'text.secondary', display: 'grid', placeItems: 'center' }}>
                    <srv.icon />
                  </Box>
                  <Chip label="Service" size="small" variant="outlined" sx={{ ml: 'auto', fontSize: '0.65rem', height: 16 }} />
                </Stack>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {srv.label}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                  {srv.desc}
                </Typography>
              </Box>
              <Typography variant="caption" color="primary" sx={{ fontWeight: 700, mt: 'auto' }}>
                Coming Soon
              </Typography>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recent Activity Table */}
      <Typography variant="h6" sx={{ fontWeight: 800, mb: 2, maxWidth: 1200, mx: 'auto' }}>
        Recent Operational Logs
      </Typography>
      <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 4, maxWidth: 1200, mx: 'auto', mb: 6 }}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead sx={{ bgcolor: '#fafafa' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 700 }}>Timestamp</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Operation/Action</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>IP Address</TableCell>
              <TableCell sx={{ fontWeight: 700 }}>Audit Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loadingData ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : activities.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                  No recent activities recorded.
                </TableCell>
              </TableRow>
            ) : (
              activities.map((act) => (
                <TableRow key={act.id} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                  <TableCell>{new Date(act.timestamp).toLocaleString()}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{act.action}</TableCell>
                  <TableCell>
                    <Chip 
                      label={act.status} 
                      color={act.status === 'SUCCESS' ? 'success' : 'error'} 
                      size="small" 
                      sx={{ fontWeight: 700, borderRadius: 2 }}
                    />
                  </TableCell>
                  <TableCell>{act.ip_address ?? 'N/A'}</TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontSize: '0.85rem' }}>
                    {JSON.stringify(act.details)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Copilot Studio Drawer */}
      <Drawer
        anchor="right"
        open={copilotOpen}
        onClose={() => setCopilotOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', sm: 480 },
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
            borderLeft: '1px solid',
            borderColor: 'divider',
          }
        }}
      >
        {/* Drawer Header */}
        <Box 
          sx={{ 
            p: 2.5, 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            background: 'linear-gradient(135deg, #7c3aed 0%, #1a73e8 100%)',
            color: 'common.white'
          }}
        >
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Avatar sx={{ bgcolor: 'common.white', color: 'primary.main' }}>
              <SmartToyRounded />
            </Avatar>
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 800, lineHeight: 1.2 }}>
                Copilot IT Assistant
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                Powered by Microsoft Copilot Studio
              </Typography>
            </Box>
          </Stack>
          <IconButton onClick={() => setCopilotOpen(false)} sx={{ color: 'common.white' }}>
            <CloseRounded />
          </IconButton>
        </Box>

        {/* Drawer Content */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', bgcolor: '#fafafa' }}>
          {copilotStudioUrl ? (
            /* Real Copilot Studio Iframe */
            <iframe
              src={copilotStudioUrl}
              title="Copilot Studio Client"
              style={{ width: '100%', height: '100%', border: 'none' }}
            />
          ) : (
            /* Mock Copilot Chat Client */
            <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {/* Message History */}
              <Box sx={{ flexGrow: 1, p: 3, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
                {messages.map((msg, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '85%',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                    }}
                  >
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 3,
                        bgcolor: msg.sender === 'user' ? 'primary.main' : 'common.white',
                        color: msg.sender === 'user' ? 'common.white' : 'text.primary',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.03)',
                        border: msg.sender === 'user' ? 'none' : '1px solid',
                        borderColor: 'divider',
                        fontSize: '0.9rem',
                        lineHeight: 1.4,
                      }}
                    >
                      {msg.text}
                    </Box>

                    {/* Render attachment action buttons if bot sent links */}
                    {msg.links && msg.links.length > 0 && (
                      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                        {msg.links.map((link, lIdx) => (
                          <Button
                            key={lIdx}
                            variant="outlined"
                            size="small"
                            onClick={() => {
                              if (link.isExternal) {
                                window.open(link.url, '_blank')
                              } else {
                                navigate(link.url)
                                setCopilotOpen(false)
                              }
                            }}
                            sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600, fontSize: '0.8rem' }}
                          >
                            {link.label}
                          </Button>
                        ))}
                      </Stack>
                    )}
                  </Box>
                ))}

                {/* Simulated Typing Indicator */}
                {isTyping && (
                  <Box sx={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 1, p: 1.5, bgcolor: 'common.white', borderRadius: 3, border: '1px solid', borderColor: 'divider' }}>
                    <CircularProgress size={16} thickness={5} />
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      Copilot is typing...
                    </Typography>
                  </Box>
                )}
                <div ref={chatEndRef} />
              </Box>

              {/* Suggestions Section */}
              <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'common.white' }}>
                <Typography variant="caption" sx={{ display: 'block', mb: 1.5, fontWeight: 700, color: 'text.secondary', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Suggestions
                </Typography>
                <Grid container spacing={1}>
                  {[
                    'How do I reset my password?',
                    'Register/Reset my MFA',
                    'Unlock my account',
                    'Request approved software'
                  ].map((sug) => (
                    <Grid key={sug} size={{ xs: 6 }}>
                      <Button
                        fullWidth
                        variant="outlined"
                        color="inherit"
                        onClick={() => handleSuggestionClick(sug)}
                        sx={{
                          justifyContent: 'flex-start',
                          textTransform: 'none',
                          textAlign: 'left',
                          fontSize: '0.75rem',
                          borderRadius: 2,
                          py: 1,
                          px: 1.5,
                          borderColor: 'divider',
                          '&:hover': { bgcolor: 'action.hover', borderColor: 'primary.light' }
                        }}
                      >
                        {sug}
                      </Button>
                    </Grid>
                  ))}
                </Grid>
              </Box>

              {/* Message Input Box */}
              <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'common.white', display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  placeholder="Type an IT question..."
                  size="small"
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSendMockMessage(inputVal)
                  }}
                  sx={{ '& .MuiOutlinedInput-root': { borderRadius: 3 } }}
                />
                <IconButton 
                  color="primary" 
                  onClick={() => handleSendMockMessage(inputVal)}
                  disabled={!inputVal.trim()}
                  sx={{ bgcolor: 'primary.main', color: 'common.white', '&:hover': { bgcolor: 'primary.dark' }, '&.Mui-disabled': { bgcolor: 'action.disabledBackground' } }}
                >
                  <SendRounded sx={{ fontSize: 18 }} />
                </IconButton>
              </Box>
            </Box>
          )}
        </Box>
      </Drawer>
    </Box>
  )
}
