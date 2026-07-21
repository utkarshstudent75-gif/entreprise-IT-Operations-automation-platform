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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  CircularProgress
} from '@mui/material'
import {
  LockRounded,
  LockOpenRounded,
  SecurityRounded,
  VpnLockRounded,
  AppShortcutRounded,
  FormatListBulletedRounded,
  SearchRounded,
  CloseRounded,
  SendRounded,
  SmartToyRounded,
  PersonRounded
} from '@mui/icons-material'
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/Header'

interface ChatMessage {
  sender: 'bot' | 'user'
  text: string
  links?: Array<{ label: string; url: string; isExternal?: boolean }>
}

export function Dashboard() {
  const navigate = useNavigate()
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Dialog & Drawer States
  const [vpnOpen, setVpnOpen] = useState(false)
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

  // Retrieve user email from localStorage
  const userEmail = localStorage.getItem('userEmail') || ''

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handlePasswordReset = () => {
    const url = `https://passwordreset.microsoftonline.com/?Username=${encodeURIComponent(userEmail)}&userId=${encodeURIComponent(userEmail)}`
    window.open(url, '_blank')
  }

  const handleMfaReset = () => {
    const url = `https://mysignins.microsoft.com/security-info?login_hint=${encodeURIComponent(userEmail)}`
    window.open(url, '_blank')
  }

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
        replyText = 'You can reset your password securely via Microsoft Self-Service Password Reset (SSPR).'
        links = [{ label: 'Go to Microsoft SSPR', url: `https://passwordreset.microsoftonline.com/?Username=${encodeURIComponent(userEmail)}`, isExternal: true }]
      } else if (query.includes('mfa') || query.includes('factor') || query.includes('auth')) {
        replyText = 'You can manage your Multi-Factor Authentication (MFA) devices and security keys securely via Microsoft Security Info.'
        links = [{ label: 'Go to Microsoft Security Info', url: `https://mysignins.microsoft.com/security-info?login_hint=${encodeURIComponent(userEmail)}`, isExternal: true }]
      } else if (query.includes('unlock')) {
        replyText = 'If your account is locked due to too many failed attempts, use our self-service unlock tool.'
        links = [{ label: 'Unlock Account Portal', url: '/dashboard/unlock-account' }]
      } else if (query.includes('software') || query.includes('request')) {
        replyText = 'You can request software licenses and automatic installations from our catalog.'
        links = [{ label: 'Request Software', url: '/dashboard/software-request' }]
      } else if (query.includes('vpn') || query.includes('network')) {
        replyText = 'VPN issues can typically be resolved by downloading the latest client or resetting your configuration. Note: VPN Self-Service tools are coming soon!'
      }

      setMessages((prev) => [...prev, { sender: 'bot', text: replyText, links }])
    }, 1000)
  }

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMockMessage(suggestion)
  }

  // Copilot studio iframe URL (if set in environment)
  const copilotStudioUrl = import.meta.env.VITE_COPILOT_STUDIO_URL || ''

  return (
    <Box>
      <Header
        title="Operations Dashboard"
        subtitle="Welcome to your corporate self-service automation console."
      />

      {/* Hero Welcome Section */}
      <Stack spacing={2} sx={{ alignItems: 'center', textAlign: 'center', mt: 4, mb: 6 }}>
        <Typography variant="h3" sx={{ fontWeight: 800, color: 'text.primary', letterSpacing: -0.5 }}>
          How can we help you?
        </Typography>

        {/* Copilot Search Bar Trigger */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            width: '100%',
            maxWidth: 600,
            px: 2.5,
            py: 1.75,
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
          <Typography color="text.secondary" sx={{ flexGrow: 1, userSelect: 'none', textAlign: 'left' }}>
            Search for help or services...
          </Typography>
          <Chip 
            label="Copilot Studio" 
            size="small" 
            color="primary" 
            sx={{ fontWeight: 700, cursor: 'pointer', borderRadius: 2 }} 
          />
        </Box>
      </Stack>

      {/* Self-Service Options Grid (3x2 layout) */}
      <Grid container spacing={3} sx={{ maxWidth: 1000, mx: 'auto', mb: 8 }}>
        {/* Card 1: Password Reset */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card 
            onClick={handlePasswordReset}
            sx={{ 
              cursor: 'pointer', 
              p: 3, 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2.5, 
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: 'none',
              transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(21, 95, 193, 0.08)',
                borderColor: 'primary.main',
              }
            }}
          >
            <Box sx={{ width: 52, height: 52, borderRadius: 3, bgcolor: '#e8f0fe', color: '#1a73e8', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <LockRounded sx={{ fontSize: 28 }} />
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary', fontSize: '1.05rem' }}>
              Password Reset
            </Typography>
          </Card>
        </Grid>

        {/* Card 2: Account Unlock */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card 
            onClick={() => navigate('/dashboard/unlock-account')}
            sx={{ 
              cursor: 'pointer', 
              p: 3, 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2.5, 
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: 'none',
              transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(21, 95, 193, 0.08)',
                borderColor: 'primary.main',
              }
            }}
          >
            <Box sx={{ width: 52, height: 52, borderRadius: 3, bgcolor: '#f3e8ff', color: '#7c3aed', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <LockOpenRounded sx={{ fontSize: 28 }} />
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary', fontSize: '1.05rem' }}>
              Account Unlock
            </Typography>
          </Card>
        </Grid>

        {/* Card 3: MFA Reset */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card 
            onClick={handleMfaReset}
            sx={{ 
              cursor: 'pointer', 
              p: 3, 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2.5, 
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: 'none',
              transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(21, 95, 193, 0.08)',
                borderColor: 'primary.main',
              }
            }}
          >
            <Box sx={{ width: 52, height: 52, borderRadius: 3, bgcolor: '#f3e8ff', color: '#7c3aed', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <SecurityRounded sx={{ fontSize: 28 }} />
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary', fontSize: '1.05rem' }}>
              MFA Reset
            </Typography>
          </Card>
        </Grid>

        {/* Card 4: VPN Issue */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card 
            onClick={() => setVpnOpen(true)}
            sx={{ 
              cursor: 'pointer', 
              p: 3, 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2.5, 
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: 'none',
              transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(21, 95, 193, 0.08)',
                borderColor: 'primary.main',
              }
            }}
          >
            <Box sx={{ width: 52, height: 52, borderRadius: 3, bgcolor: '#e0f2f1', color: '#00695c', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <VpnLockRounded sx={{ fontSize: 28 }} />
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary', fontSize: '1.05rem' }}>
              VPN Issue
            </Typography>
          </Card>
        </Grid>

        {/* Card 5: Software Request */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card 
            onClick={() => navigate('/dashboard/software-request')}
            sx={{ 
              cursor: 'pointer', 
              p: 3, 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2.5, 
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: 'none',
              transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(21, 95, 193, 0.08)',
                borderColor: 'primary.main',
              }
            }}
          >
            <Box sx={{ width: 52, height: 52, borderRadius: 3, bgcolor: '#f3e8ff', color: '#9333ea', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <AppShortcutRounded sx={{ fontSize: 28 }} />
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary', fontSize: '1.05rem' }}>
              Software Request
            </Typography>
          </Card>
        </Grid>

        {/* Card 6: Other Requests */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card 
            onClick={() => navigate('/dashboard/my-requests')}
            sx={{ 
              cursor: 'pointer', 
              p: 3, 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2.5, 
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: 'none',
              transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 24px rgba(21, 95, 193, 0.08)',
                borderColor: 'primary.main',
              }
            }}
          >
            <Box sx={{ width: 52, height: 52, borderRadius: 3, bgcolor: '#f1f3f4', color: '#5f6368', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <FormatListBulletedRounded sx={{ fontSize: 28 }} />
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.primary', fontSize: '1.05rem' }}>
              Other Requests
            </Typography>
          </Card>
        </Grid>
      </Grid>

      {/* VPN Help Dialog */}
      <Dialog open={vpnOpen} onClose={() => setVpnOpen(false)} sx={{ '& .MuiPaper-root': { borderRadius: 4, p: 1 } }}>
        <DialogTitle sx={{ fontWeight: 800 }}>VPN Issue Resolution</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            To resolve VPN connectivity issues, please ensure:
          </DialogContentText>
          <Box component="ul" sx={{ pl: 2, mb: 2, '& li': { mb: 1, fontSize: '0.9rem', color: 'text.secondary' } }}>
            <li>Your local internet connection is active and stable.</li>
            <li>You are using the latest version of the Cisco Secure Client.</li>
            <li>Your MFA device is ready to approve the push notification.</li>
          </Box>
          <DialogContentText color="primary" sx={{ fontWeight: 600 }}>
            Self-service automatic VPN re-provisioning tools are coming soon! For urgent help, please contact the IT Helpdesk at support@enterprise.com.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={() => setVpnOpen(false)} variant="contained" sx={{ borderRadius: 2 }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

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
