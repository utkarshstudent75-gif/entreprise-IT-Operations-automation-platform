import { useCallback, useEffect, useState, type FormEvent } from 'react'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { Header } from '../../components/Header'
import { useAuth } from '../../contexts/AuthContext'
import {
  createAccountUnlockRequest,
  getPendingAccountUnlockRequests,
  getOperationsApiError,
  type AccountUnlockRequest,
} from '../../api/operationsApi'

export function UnlockAccount() {
  const { getAccessToken, user } = useAuth()
  const [email, setEmail] = useState(user?.email ?? '')
  const [justification, setJustification] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [pendingRequests, setPendingRequests] = useState<AccountUnlockRequest[]>([])
  const [queueLoading, setQueueLoading] = useState(false)
  const [queueError, setQueueError] = useState('')
  const isApprover = user?.role === 'Platform Administrator' || user?.role === 'Support Engineer'

  const loadPendingRequests = useCallback(async () => {
    if (!isApprover) return
    setQueueLoading(true)
    try {
      const token = await getAccessToken()
      if (!token) throw new Error('Your session has expired. Sign in again.')
      setPendingRequests(await getPendingAccountUnlockRequests(token))
      setQueueError('')
    } catch (requestError) {
      setQueueError(getOperationsApiError(requestError, 'Unable to load pending unlock requests.'))
    } finally {
      setQueueLoading(false)
    }
  }, [getAccessToken, isApprover])

  useEffect(() => {
    void loadPendingRequests()
  }, [loadPendingRequests])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      const token = await getAccessToken()
      if (!token) throw new Error('Your session has expired. Sign in again.')
      const request = await createAccountUnlockRequest(token, email, justification)
      setSuccess(`Unlock request #${request.id} was recorded for manual review.`)
      setJustification('')
      await loadPendingRequests()
    } catch (requestError) {
      setError(getOperationsApiError(requestError, 'Unable to submit your request.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Header title="Unlock Account" breadcrumbs={[{ label: 'Unlock Account' }]} />
      <Paper
        component="form"
        onSubmit={submit}
        elevation={0}
        sx={{ p: { xs: 2, md: 4 }, border: '1px solid', borderColor: 'divider', borderRadius: 3 }}
      >
        <Stack spacing={2.5} maxWidth={640}>
          <Typography variant="h5" sx={{ fontWeight: 800 }}>
            Request account unlock
          </Typography>
          <Alert severity="info">
            Microsoft Graph does not provide a safe action to clear sign-in
            lockout. This request is verified against your signed-in identity
            and routed to IT for manual handling.
          </Alert>
          {error && <Alert severity="error">{error}</Alert>}
          {success && <Alert severity="success">{success}</Alert>}
          <TextField
            label="Your work email"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
          />
          <TextField
            label="Why do you need an unlock?"
            required
            multiline
            minRows={3}
            inputProps={{ maxLength: 1000 }}
            value={justification}
            onChange={(event) => setJustification(event.target.value)}
          />
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Submitting…' : 'Submit unlock request'}
          </Button>
        </Stack>
      </Paper>
      {isApprover && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
            Pending unlock requests
          </Typography>
          {queueError && <Alert severity="error" sx={{ mb: 2 }}>{queueError}</Alert>}
          {queueLoading ? (
            <CircularProgress size={28} />
          ) : pendingRequests.length === 0 ? (
            <Typography color="text.secondary">There are no pending unlock requests.</Typography>
          ) : (
            <Stack spacing={1.5}>
              {pendingRequests.map((request) => (
                <Paper
                  key={request.id}
                  elevation={0}
                  sx={{ p: 2.5, border: '1px solid', borderColor: 'divider' }}
                >
                  <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" spacing={1}>
                    <Box>
                      <Typography sx={{ fontWeight: 700 }}>{request.requester_email}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {request.justification}
                      </Typography>
                    </Box>
                    <Chip label="PENDING - MANUAL" color="warning" />
                  </Stack>
                </Paper>
              ))}
            </Stack>
          )}
        </Box>
      )}
    </Box>
  )
}
