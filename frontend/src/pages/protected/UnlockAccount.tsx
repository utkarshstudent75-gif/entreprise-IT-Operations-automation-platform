import { Box, Paper, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/Header'

export function UnlockAccount() {
  const navigate = useNavigate()

  return (
    <Box>
      <Header
        title="Unlock Account"
        breadcrumbs={[{ label: 'Unlock Account' }]}
      />
      <Paper elevation={0} sx={{ p: 4, border: '1px solid', borderColor: 'divider', borderRadius: 3, textAlign: 'center' }}>
        <Typography variant="h5" sx={{ fontWeight: 800, mb: 1 }}>
          Unlock Account
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Self-service unlock if your account has been locked due to excessive failed attempts.
        </Typography>
        <Typography variant="h6" color="primary" sx={{ fontWeight: 700, mb: 3 }}>
          Coming Soon
        </Typography>
        <Button variant="outlined" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
      </Paper>
    </Box>
  )
}
