import { Box, Paper, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/Header'

export function MyRequests() {
  const navigate = useNavigate()

  return (
    <Box>
      <Header
        title="My Requests"
        breadcrumbs={[{ label: 'My Requests' }]}
      />
      <Paper elevation={0} sx={{ p: 4, border: '1px solid', borderColor: 'divider', borderRadius: 3, textAlign: 'center' }}>
        <Typography variant="h5" sx={{ fontWeight: 800, mb: 1 }}>
          My Requests
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Monitor the completion status of your active software and access requests.
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
