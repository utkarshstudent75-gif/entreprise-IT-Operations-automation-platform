import type { FormEvent } from 'react'
import { useState } from 'react'
import { Box, Button, Container, Paper, Stack, TextField, Typography } from '@mui/material'

import { createUser } from '../api/userApi'
import { StatusAlert, type AlertSeverity } from '../components/StatusAlert'

export function CreateUserPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [message, setMessage] = useState('')
  const [severity, setSeverity] = useState<AlertSeverity>('info')

  const resetForm = () => {
    setUsername('')
    setEmail('')
    setPassword('')
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSubmitting(true)
    setMessage('')

    try {
      const result = await createUser({
        username: username.trim(),
        email: email.trim(),
        password,
      })

      if (result.success) {
        setMessage(result.message)
        setSeverity('success')
        resetForm()
      } else {
        setMessage(result.message)
        setSeverity('error')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Box sx={{ alignItems: 'center', bgcolor: '#f5f8ff', display: 'flex', minHeight: '100vh', py: 4 }}>
      <Container maxWidth="sm">
        <Paper elevation={4} sx={{ borderRadius: 3, p: 4 }}>
          <Stack spacing={3}>
            <Stack spacing={1}>
              <Typography color="primary" fontWeight={800} letterSpacing={1.2} textTransform="uppercase">
                Create User
              </Typography>
              <Typography variant="h4" fontWeight={700}>
                Add a new account
              </Typography>
              <Typography color="text.secondary" sx={{ lineHeight: 1.65 }}>
                Enter a username, email, and secure password to create a new user in the system.
              </Typography>
            </Stack>

            <Box component="form" onSubmit={handleSubmit} noValidate>
              <Stack spacing={2}>
                <TextField
                  label="Username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  required
                  fullWidth
                />

                <TextField
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  fullWidth
                />

                <TextField
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  fullWidth
                />

                <Button disabled={isSubmitting} fullWidth size="large" type="submit" variant="contained">
                  {isSubmitting ? 'Creating user...' : 'Create user'}
                </Button>
              </Stack>
            </Box>

            <StatusAlert message={message} severity={severity} />
          </Stack>
        </Paper>
      </Container>
    </Box>
  )
}
