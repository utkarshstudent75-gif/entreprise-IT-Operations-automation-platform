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
  createSoftwareRequest,
  getMySoftwareRequests,
  getOperationsApiError,
  type SoftwareRequest as SoftwareRequestItem,
} from '../../api/operationsApi'

export function SoftwareRequest() {
  const { getAccessToken } = useAuth()
  const [softwareName, setSoftwareName] = useState('')
  const [justification, setJustification] = useState('')
  const [requests, setRequests] = useState<SoftwareRequestItem[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadRequests = useCallback(async () => {
    try {
      const token = await getAccessToken()
      if (!token) throw new Error('Your session has expired. Sign in again.')
      setRequests(await getMySoftwareRequests(token))
      setError('')
    } catch (requestError) {
      setError(getOperationsApiError(requestError, 'Unable to load your requests.'))
    } finally {
      setLoading(false)
    }
  }, [getAccessToken])

  useEffect(() => {
    void loadRequests()
  }, [loadRequests])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setSuccess('')
    try {
      const token = await getAccessToken()
      if (!token) throw new Error('Your session has expired. Sign in again.')
      await createSoftwareRequest(token, softwareName, justification)
      setSoftwareName('')
      setJustification('')
      setSuccess('Your request was submitted for approval.')
      await loadRequests()
    } catch (requestError) {
      setError(getOperationsApiError(requestError, 'Unable to submit your request.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Box>
      <Header title="Software Request" breadcrumbs={[{ label: 'Software Request' }]} />
      <Paper
        component="form"
        onSubmit={submit}
        elevation={0}
        sx={{ p: { xs: 2, md: 4 }, mb: 3, border: '1px solid', borderColor: 'divider', borderRadius: 3 }}
      >
        <Stack spacing={2.5} maxWidth={720}>
          <Typography variant="h5" sx={{ fontWeight: 800 }}>
            Request software
          </Typography>
          <Typography color="text.secondary">
            Your request will be reviewed by an authorized IT approver. Approval
            does not automatically install software.
          </Typography>
          {error && <Alert severity="error">{error}</Alert>}
          {success && <Alert severity="success">{success}</Alert>}
          <TextField
            label="Software name"
            required
            inputProps={{ maxLength: 255 }}
            value={softwareName}
            onChange={(event) => setSoftwareName(event.target.value)}
          />
          <TextField
            label="Business justification"
            required
            multiline
            minRows={3}
            inputProps={{ maxLength: 1000 }}
            value={justification}
            onChange={(event) => setJustification(event.target.value)}
          />
          <Button type="submit" variant="contained" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit request'}
          </Button>
        </Stack>
      </Paper>

      <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
        My requests
      </Typography>
      {loading ? (
        <CircularProgress size={28} />
      ) : requests.length === 0 ? (
        <Typography color="text.secondary">You have no software requests.</Typography>
      ) : (
        <Stack spacing={1.5}>
          {requests.map((request) => (
            <Paper key={request.id} elevation={0} sx={{ p: 2.5, border: '1px solid', borderColor: 'divider' }}>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                justifyContent="space-between"
                spacing={1}
              >
                <Box>
                  <Typography sx={{ fontWeight: 700 }}>{request.software_name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {request.justification}
                  </Typography>
                </Box>
                <Chip label={request.status} color={request.status === 'PENDING' ? 'warning' : request.status === 'APPROVED' ? 'success' : 'default'} />
              </Stack>
            </Paper>
          ))}
        </Stack>
      )}
    </Box>
  )
}
