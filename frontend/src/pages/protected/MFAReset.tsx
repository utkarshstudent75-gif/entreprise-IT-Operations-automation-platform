import { Box, Paper, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/Header'

export function MFAReset() {
  const navigate = useNavigate()

  return (
    <Box>
      <Header
        title="MFA Reset"
        breadcrumbs={[{ label: 'MFA Reset' }]}
      />
      <Paper elevation={0} sx={{ p: 4, border: '1px solid', borderColor: 'divider', borderRadius: 3, textAlign: 'center' }}>
        <Typography variant="h5" sx={{ fontWeight: 800, mb: 1 }}>
          MFA Reset
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Reset or register new Multi-Factor Authentication (MFA) devices and security keys.
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
