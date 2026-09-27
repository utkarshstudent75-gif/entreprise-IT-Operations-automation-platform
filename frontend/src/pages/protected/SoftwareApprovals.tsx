import { useCallback, useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material'
import { Header } from '../../components/Header'
import { useAuth } from '../../contexts/AuthContext'
import {
  decideSoftwareRequest,
  getOperationsApiError,
  getPendingSoftwareRequests,
  type SoftwareRequest,
} from '../../api/operationsApi'

export function SoftwareApprovals() {
  const { getAccessToken } = useAuth()
  const [requests, setRequests] = useState<SoftwareRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [activeRequest, setActiveRequest] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadRequests = useCallback(async (clearError = true) => {
    try {
      const token = await getAccessToken()
      if (!token) throw new Error('Your session has expired. Sign in again.')
      setRequests(await getPendingSoftwareRequests(token))
      if (clearError) setError('')
    } catch (requestError) {
      setError(getOperationsApiError(requestError, 'Unable to load pending requests.'))
    } finally {
      setLoading(false)
    }
  }, [getAccessToken])

  useEffect(() => {
    void loadRequests()
  }, [loadRequests])

  const decide = async (requestId: number, decision: 'approve' | 'reject') => {
    setActiveRequest(requestId)
    setError('')
    setSuccess('')
    try {
      const token = await getAccessToken()
      if (!token) throw new Error('Your session has expired. Sign in again.')
      await decideSoftwareRequest(token, requestId, decision)
      setSuccess(`Request ${decision === 'approve' ? 'approved' : 'rejected'}.`)
    } catch (requestError) {
      setError(getOperationsApiError(requestError, 'Unable to record the decision.'))
    } finally {
      await loadRequests(false)
      setActiveRequest(null)
    }
  }

  return (
    <Box>
      <Header title="Software Approvals" breadcrumbs={[{ label: 'Software Approvals' }]} />
      <Stack spacing={2}>
        <Typography color="text.secondary">
          Review employee requests. A decision is final and cannot be changed.
        </Typography>
        {error && <Alert severity="error">{error}</Alert>}
        {success && <Alert severity="success">{success}</Alert>}
        {loading ? (
          <CircularProgress size={28} />
        ) : requests.length === 0 ? (
          <Typography color="text.secondary">There are no pending software requests.</Typography>
        ) : (
          requests.map((request) => (
            <Paper
              key={request.id}
              elevation={0}
              sx={{ p: 2.5, border: '1px solid', borderColor: 'divider' }}
            >
              <Stack spacing={1.5}>
                <Stack direction="row" justifyContent="space-between" spacing={2}>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    {request.software_name}
                  </Typography>
                  <Chip label={request.status} color="warning" />
                </Stack>
                <Typography variant="body2">
                  Requester: {request.requester_email ?? 'Unknown requester'}
                </Typography>
                <Typography color="text.secondary">{request.justification}</Typography>
                <Stack direction="row" spacing={1}>
                  <Button
                    variant="contained"
                    disabled={activeRequest !== null}
                    onClick={() => void decide(request.id, 'approve')}
                  >
                    {activeRequest === request.id ? 'Saving...' : 'Approve'}
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    disabled={activeRequest !== null}
                    onClick={() => void decide(request.id, 'reject')}
                  >
                    Reject
                  </Button>
                </Stack>
              </Stack>
            </Paper>
          ))
        )}
      </Stack>
    </Box>
  )
}
