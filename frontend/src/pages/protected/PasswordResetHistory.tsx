import { Box, Card, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, CircularProgress, Alert } from '@mui/material'
import { HistoryRounded } from '@mui/icons-material'
import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { Header } from '../../components/Header'
import axios from 'axios'

interface ResetEvent {
  id: number
  timestamp: string
  action: string
  status: string
  ip_address: string
  request_id: string
  details: {
    email: string
    reason?: string
  }
}

export function PasswordResetHistory() {
  const { getAccessToken, user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [history, setHistory] = useState<ResetEvent[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true)
      setError('')
      try {
        const token = await getAccessToken()
        const apiBase = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
        
        const { data } = await axios.get(`${apiBase}/password/reset-history`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        
        if (data?.success) {
          setHistory(data.data)
        } else {
          setError(data?.message ?? 'Failed to load history.')
        }
      } catch (err: any) {
        console.error('Failed to load password history:', err)
        setError(err?.response?.data?.detail ?? 'An error occurred while fetching password reset history.')
      } finally {
        setLoading(false)
      }
    }

    if (user) {
      fetchHistory()
    }
  }, [getAccessToken, user])

  const formatActionName = (action: string) => {
    switch (action) {
      case 'password_reset_requested':
        return 'OTP Requested'
      case 'otp_verified':
        return 'OTP Verified'
      case 'graph_password_reset_initiated':
        return 'Reset Initiated'
      case 'graph_password_reset_successful':
        return 'Reset Successful'
      case 'graph_password_reset_failed':
        return 'Reset Failed'
      default:
        return action.replace(/_/g, ' ')
    }
  }

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleString()
  }

  return (
    <Box>
      <Header
        title="Password Reset History"
        subtitle={
          user?.role === 'Platform Administrator' || user?.role === 'Auditor'
            ? 'Review the global password reset logs across the enterprise.'
            : 'Track the status and security audits of your own password reset requests.'
        }
        breadcrumbs={[{ label: 'User Center' }, { label: 'Reset History' }]}
      />

      <Card
        sx={{
          p: 4,
          mt: 3,
          borderRadius: 4,
          border: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
          <HistoryRounded color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            Audit Log Entries
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 5 }}>
            <CircularProgress />
          </Box>
        ) : history.length === 0 ? (
          <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 4 }}>
            No password reset logs found.
          </Typography>
        ) : (
          <TableContainer>
            <Table sx={{ minWidth: 650 }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Timestamp</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Target User</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Action</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>IP Address</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Correlation ID</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Details</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((row) => (
                  <TableRow key={row.id} hover>
                    <TableCell sx={{ fontSize: '0.85rem' }}>{formatTime(row.timestamp)}</TableCell>
                    <TableCell sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
                      {row.details?.email ?? 'N/A'}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.85rem' }}>{formatActionName(row.action)}</TableCell>
                    <TableCell>
                      <Chip
                        label={row.status}
                        color={row.status === 'SUCCESS' ? 'success' : 'error'}
                        size="small"
                        sx={{ fontWeight: 700, borderRadius: 1.5, fontSize: '0.75rem' }}
                      />
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.85rem', fontFamily: 'monospace' }}>
                      {row.ip_address ?? 'N/A'}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.85rem', fontFamily: 'monospace' }}>
                      {row.request_id ? `${row.request_id.substring(0, 8)}...` : 'N/A'}
                    </TableCell>
                    <TableCell sx={{ fontSize: '0.85rem', color: 'text.secondary' }}>
                      {row.status === 'FAILED' ? (row.details?.reason ?? 'Unknown Error') : 'Completed'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>
    </Box>
  )
}
