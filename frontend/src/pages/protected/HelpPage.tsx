import { Box, Paper, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/Header'

export function HelpPage() {
  const navigate = useNavigate()

  return (
    <Box>
      <Header
        title="Help & Support"
        breadcrumbs={[{ label: 'Help' }]}
      />
      <Paper elevation={0} sx={{ p: 4, border: '1px solid', borderColor: 'divider', borderRadius: 3, textAlign: 'center' }}>
        <Typography variant="h5" sx={{ fontWeight: 800, mb: 1 }}>
          Help Center & Support Desk
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Access documentation, view system status details, or request help from IT support administrators.
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
