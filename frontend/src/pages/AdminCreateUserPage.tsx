import { Box, Stack, Typography } from '@mui/material'
import { useState } from 'react'

import { createUser } from '../api/userApi'
import { EnterpriseCard } from '../components/EnterpriseCard'
import { FormAlert } from '../components/FormAlert'
import { LoadingButton } from '../components/LoadingButton'
import { PasswordInput } from '../components/PasswordInput'
import { TextInput } from '../components/TextInput'

export function AdminCreateUserPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [statusSeverity, setStatusSeverity] = useState<'success' | 'error' | 'info'>('info')
  const [loading, setLoading] = useState(false)

  const validEmail = email.includes('@') && email.includes('.')
  const validPassword = password.length >= 8
  const validUsername = username.trim().length >= 3

  const handleCreateUser = async () => {
    setStatusMessage('')
    setLoading(true)
    try {
      const response = await createUser({ username: username.trim(), email: email.trim(), password })
      setStatusMessage(response.message)
      setStatusSeverity(response.success ? 'success' : 'error')
      if (response.success) {
        setUsername('')
        setEmail('')
        setPassword('')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
      <Box sx={{ width: '100%', maxWidth: 900 }}>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
          Administrator Tools
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Create a new user account for internal testing and administration.
        </Typography>

        <EnterpriseCard>
          <Stack spacing={3}>
            <FormAlert open={Boolean(statusMessage)} severity={statusSeverity}>
              {statusMessage}
            </FormAlert>
            <Stack spacing={2}>
              <TextInput
                label="Username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                helperText="Enter a unique username for the new user."
              />
              <TextInput
                label="Email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                helperText="The user’s work email address."
              />
              <PasswordInput
                label="Password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                helperText="Minimum 8 characters recommended."
              />
              <LoadingButton
                variant="contained"
                loading={loading}
                disabled={!validUsername || !validEmail || !validPassword}
                onClick={handleCreateUser}
              >
                Create user
              </LoadingButton>
            </Stack>
          </Stack>
        </EnterpriseCard>
      </Box>
    </Box>
  )
}
