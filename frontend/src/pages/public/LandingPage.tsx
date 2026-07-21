import { Box, Button, Card, Divider, Grid, Stack, Typography } from '@mui/material'
import {
  LockOpenRounded,
  SupportAgentRounded,
  CheckCircleRounded,
  ChevronRightRounded,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

export function LandingPage() {
  const navigate = useNavigate()

  return (
    <Box sx={{ py: { xs: 4, md: 8 } }}>
      <Grid container spacing={5} alignItems="center">
        {/* Left Side: Message & Branding */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Stack spacing={3}>
            {/* Branding Logo Placeholder */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  width: 52,
                  height: 52,
                  borderRadius: 2,
                  bgcolor: 'primary.main',
                  display: 'grid',
                  placeItems: 'center',
                  boxShadow: '0 4px 14px rgba(21, 95, 193, 0.25)',
                }}
              >
                <Typography variant="h5" sx={{ color: 'common.white', fontWeight: 800 }}>
                  E
                </Typography>
              </Box>
              <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 600 }}>
                Enterprise Corp IT
              </Typography>
            </Box>

            <Typography
              variant="h2"
              component="h1"
              sx={{
                fontWeight: 900,
                letterSpacing: '-0.03em',
                lineHeight: 1.1,
                fontSize: { xs: '2.5rem', sm: '3.5rem' },
              }}
            >
              Enterprise IT Operations Portal
            </Typography>

            <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 400, lineHeight: 1.6, maxWidth: 600 }}>
              Access Identity Services, software provisioning, and request corporate resources from a single, integrated IT operations center.
            </Typography>

            {/* Quick trust metrics or status placeholder */}
            <Stack direction="row" spacing={3} divider={<Divider orientation="vertical" flexItem />}>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 800, color: 'primary.main' }}>
                  99.9%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Service Uptime
                </Typography>
              </Box>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 800, color: 'primary.main' }}>
                  24/7
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  IT Support Available
                </Typography>
              </Box>
            </Stack>
          </Stack>
        </Grid>

        {/* Right Side: Navigation Card / Quick Actions */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card
            elevation={4}
            sx={{
              p: 4,
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              bgcolor: 'common.white',
            }}
          >
            <Stack spacing={3}>
              <Typography variant="h5" sx={{ fontWeight: 800, letterSpacing: '-0.015em' }}>
                Welcome to IT Self-Service
              </Typography>

              {/* System Status Placeholder */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: '#e6f4ea',
                  color: '#137333',
                  border: '1px solid #ceead6',
                }}
              >
                <CheckCircleRounded sx={{ fontSize: 20 }} />
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  System Status: All Services Operational
                </Typography>
              </Box>

              {/* Primary button: Sign In */}
              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={() => navigate('/login')}
                sx={{ py: 1.5 }}
                endIcon={<ChevronRightRounded />}
              >
                Sign In to Dashboard
              </Button>

              {/* Secondary section: Can't sign in? Reset Password */}
              <Box sx={{ py: 1 }}>
                <Divider sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
                    Can't sign in?
                  </Typography>
                </Divider>
                <Button
                  variant="outlined"
                  size="medium"
                  fullWidth
                  onClick={() => navigate('/password-reset')}
                  startIcon={<LockOpenRounded />}
                  sx={{ py: 1.2 }}
                >
                  Reset Corporate Password
                </Button>
              </Box>

              <Divider />

              {/* Contact IT Support placeholder */}
              <Stack direction="row" spacing={2} alignItems="center" sx={{ color: 'text.secondary' }}>
                <SupportAgentRounded sx={{ fontSize: 24, color: 'primary.main' }} />
                <Box>
                  <Typography variant="caption" sx={{ fontWeight: 600, display: 'block', textTransform: 'uppercase', color: 'text.secondary' }}>
                    IT Helpdesk
                  </Typography>
                  <Typography variant="body2" color="text.primary">
                    support@enterprise.com | +1 (800) 555-0199
                  </Typography>
                </Box>
              </Stack>
            </Stack>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
