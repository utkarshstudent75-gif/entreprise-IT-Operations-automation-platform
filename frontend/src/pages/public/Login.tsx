import { Box, Button, Card, Stack, TextField, Typography, Link, Alert } from '@mui/material'
import { useState } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export function Login() {
  const { authProvider, login, loginWithMicrosoft } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields.')
      return
    }

    setLoading(true)
    try {
      await login(email.trim(), password)
      navigate('/dashboard')
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Invalid email or password.'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleMicrosoftLogin = async () => {
    setError('')
    try {
      await loginWithMicrosoft()
    } catch {
      setError('Microsoft sign in failed. Please try again.')
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
              {authProvider === 'local'
                ? 'Use your corporate credentials to sign in'
                : 'Sign in using your Enterprise Identity provider'}
            </Typography>
          </Box>

          {error && <Alert severity="error">{error}</Alert>}

          {authProvider === 'local' ? (
            <>
              <TextField
                label="Corporate Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                fullWidth
                required
                autoComplete="email"
                autoFocus
                disabled={loading}
              />

              <TextField
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                fullWidth
                required
                autoComplete="current-password"
                disabled={loading}
              />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Link
                  component={RouterLink}
                  to="/password-reset"
                  variant="body2"
                  sx={{ fontWeight: 600 }}
                >
                  Forgot Password?
                </Link>
              </Box>

              <Button type="submit" variant="contained" size="large" fullWidth sx={{ py: 1.25 }} disabled={loading}>
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>
            </>
          ) : (
            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={handleMicrosoftLogin}
              sx={{
                py: 1.5,
                bgcolor: '#2f2f2f',
                color: '#fff',
                '&:hover': { bgcolor: '#000' },
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 1.5,
                borderRadius: 2,
                boxShadow: 2,
              }}
            >
              <svg width="20" height="20" viewBox="0 0 21 21" style={{ marginRight: 8 }}>
                <rect x="1" y="1" width="9" height="9" fill="#f25022" />
                <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
                <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
                <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
              </svg>
              Sign in with Microsoft
            </Button>
          )}

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

