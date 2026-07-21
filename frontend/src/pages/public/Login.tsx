import { Box, Button, Card, Stack, TextField, Typography, Link, Alert } from '@mui/material'
import { useState } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'

export function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields.')
      return
    }

    // Mock Login Success
    localStorage.setItem('isAuthenticated', 'true')
    localStorage.setItem('userEmail', email.trim())
    navigate('/dashboard')
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
              Use your corporate credentials to sign in
            </Typography>
          </Box>

          {error && <Alert severity="error">{error}</Alert>}

          <TextField
            label="Corporate Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            required
            autoComplete="email"
            autoFocus
          />

          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            required
            autoComplete="current-password"
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

          <Button type="submit" variant="contained" size="large" fullWidth sx={{ py: 1.25 }}>
            Sign In
          </Button>

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
