import { Box, Button, Card, Stack, TextField, Typography, Link, Alert, MenuItem, Select, FormControl, InputLabel } from '@mui/material'
import { useState, useEffect } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import { useAuth, UserProfile } from '../../contexts/AuthContext'

export function Login() {
  const navigate = useNavigate()
  const { login, isAuthenticated, isMockMode } = useAuth()
  
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<UserProfile['role']>('Standard User')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard')
    }
  }, [isAuthenticated, navigate])

  // Automatically trigger Microsoft Entra SSO redirect if not in mock mode and not authenticated
  useEffect(() => {
    if (!isMockMode && !isAuthenticated) {
      setLoading(true)
      login().catch((err: unknown) => {
        setError((err as Error)?.message ?? 'Automatic Entra ID login redirect failed.')
        setLoading(false)
      })
    }
  }, [isAuthenticated, isMockMode, login])

  // Set default test email depending on role selected
  useEffect(() => {
    if (isMockMode) {
      if (role === 'Platform Administrator') {
        setEmail('riya@example.com')
      } else if (role === 'Support Engineer') {
        setEmail('support@example.com')
      } else if (role === 'Auditor') {
        setEmail('auditor@example.com')
      } else {
        setEmail('arsh@example.com')
      }
    }
  }, [role, isMockMode])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isMockMode) {
        if (!email.trim()) {
          setError('Please enter an email address.')
          setLoading(false)
          return
        }
        await login({ email: email.trim(), role })
      } else {
        await login()
      }
      navigate('/dashboard')
    } catch (err: unknown) {
      setError((err as Error)?.message ?? 'Authentication failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', py: { xs: 2, md: 5 } }}>
      <Card
        elevation={3}
        sx={{
          p: 4,
          width: '100%',
          maxWidth: 450,
          borderRadius: 4,
          border: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Stack spacing={3} component="form" onSubmit={handleLogin} noValidate>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" component="h1" sx={{ fontWeight: 800, mb: 1 }}>
              Portal Sign In
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {isMockMode 
                ? 'Local development mock SSO mode enabled' 
                : 'Use your corporate credentials to sign in via Microsoft SSO'}
            </Typography>
          </Box>

          {error && <Alert severity="error">{error}</Alert>}

          {isMockMode ? (
            <>
              <FormControl fullWidth required>
                <InputLabel id="developer-role-label">Developer Role</InputLabel>
                <Select
                  labelId="developer-role-label"
                  value={role}
                  label="Developer Role"
                  onChange={(e) => setRole(e.target.value as UserProfile['role'])}
                >
                  <MenuItem value="Standard User">Standard User</MenuItem>
                  <MenuItem value="Platform Administrator">Platform Administrator</MenuItem>
                  <MenuItem value="Support Engineer">Support Engineer</MenuItem>
                  <MenuItem value="Auditor">Auditor</MenuItem>
                </Select>
              </FormControl>

              <TextField
                label="Mock Corporate Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                fullWidth
                required
                autoComplete="email"
              />

              <Button 
                type="submit" 
                variant="contained" 
                size="large" 
                fullWidth 
                disabled={loading}
                sx={{ py: 1.25 }}
              >
                {loading ? 'Signing in...' : 'Sign In (Mock Bypass)'}
              </Button>
            </>
          ) : (
            <Button
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              disabled={loading}
              sx={{
                py: 1.5,
                bgcolor: '#0078d4', // Microsoft blue
                fontWeight: 700,
                fontSize: '1rem',
                textTransform: 'none',
                '&:hover': {
                  bgcolor: '#005a9e',
                }
              }}
            >
              {loading ? 'Connecting...' : 'Sign In with Microsoft'}
            </Button>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Link
              component={RouterLink}
              to="/password-reset"
              variant="body2"
              sx={{ fontWeight: 600 }}
            >
              Self-Service Password Reset
            </Link>
          </Box>

          <Box sx={{ textAlign: 'center' }}>
            <Link component={RouterLink} to="/" variant="body2" sx={{ fontWeight: 600 }}>
              Back to Landing Page
            </Link>
          </Box>
        </Stack>
      </Card>
    </Box>
  )
}

