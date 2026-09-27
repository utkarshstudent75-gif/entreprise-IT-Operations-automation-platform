import { useState, type FormEvent } from 'react'
import { Alert, Box, Button, Paper, Stack, TextField, Typography } from '@mui/material'
import { Header } from '../../components/Header'
import { useAuth } from '../../contexts/AuthContext'
import { getOperationsApiError, resetMfa } from '../../api/operationsApi'

export function MFAReset() {
  const { getAccessToken, user } = useAuth()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const token = await getAccessToken()
      if (!token) throw new Error('Your session has expired. Sign in again.')
      setSuccess(await resetMfa(token, email))
      setEmail('')
    } catch (requestError) {
      setError(getOperationsApiError(requestError, 'Unable to reset MFA methods.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Header title="MFA Reset" breadcrumbs={[{ label: 'MFA Reset' }]} />
      <Paper
        component="form"
        onSubmit={submit}
        elevation={0}
        sx={{ p: { xs: 2, md: 4 }, border: '1px solid', borderColor: 'divider', borderRadius: 3 }}
      >
        <Stack spacing={2.5} maxWidth={640}>
          <Typography variant="h5" sx={{ fontWeight: 800 }}>
            Reset your registered MFA methods
          </Typography>
          <Typography color="text.secondary">
            Supported non-password methods will be removed from your Entra
            account. You will need to register MFA again at your next sign-in.
          </Typography>
          {error && <Alert severity="error">{error}</Alert>}
          {success && <Alert severity="success">{success}</Alert>}
          <TextField
            label="Confirm your signed-in work email"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            helperText={`Signed in as ${user?.email ?? ''}`}
          />
          <Button type="submit" variant="contained" color="warning" disabled={loading}>
            {loading ? 'Resetting…' : 'Reset MFA methods'}
          </Button>
        </Stack>
      </Paper>
    </Box>
  )
}
