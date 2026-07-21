import { Box, Stack, Typography, Button, CircularProgress } from '@mui/material'
import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { LockResetRounded } from '@mui/icons-material'
import { EnterpriseCard } from '../../components/EnterpriseCard'

export function PasswordReset() {
  const [countdown, setCountdown] = useState(2)
  const MICROSOFT_SSPR_URL = 'https://passwordreset.microsoftonline.com/'

  useEffect(() => {
    if (countdown <= 0) {
      window.location.href = MICROSOFT_SSPR_URL
      return
    }

    const timer = setTimeout(() => {
      setCountdown((prev) => prev - 1)
    }, 1000)

    return () => clearTimeout(timer)
  }, [countdown])

  const handleManualRedirect = () => {
    window.location.href = MICROSOFT_SSPR_URL
  }

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', py: { xs: 4, md: 8 } }}>
      <Box sx={{ width: '100%', maxWidth: 550 }}>
        <EnterpriseCard>
          <Stack spacing={4} alignItems="center" sx={{ py: 2, textAlign: 'center' }}>
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                bgcolor: 'primary.light',
                color: 'primary.contrastText',
                display: 'grid',
                placeItems: 'center',
                boxShadow: '0 8px 16px rgba(21, 95, 193, 0.2)',
              }}
            >
              <LockResetRounded sx={{ fontSize: 36 }} />
            </Box>

            <Stack spacing={1}>
              <Typography variant="h5" sx={{ fontWeight: 800 }}>
                Redirecting to Microsoft SSPR
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ px: 2 }}>
                Your corporate password is managed securely through Microsoft Active Directory. 
                You are being redirected to the Microsoft Self-Service Password Reset (SSPR) portal.
              </Typography>
            </Stack>

            <Box sx={{ position: 'relative', display: 'inline-flex', my: 2 }}>
              <CircularProgress size={60} thickness={4} />
              <Box
                sx={{
                  top: 0,
                  left: 0,
                  bottom: 0,
                  right: 0,
                  position: 'absolute',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Typography variant="caption" component="div" color="text.secondary" sx={{ fontWeight: 700 }}>
                  {countdown}s
                </Typography>
              </Box>
            </Box>

            <Stack spacing={2} sx={{ width: '100%' }}>
              <Button
                variant="contained"
                size="large"
                onClick={handleManualRedirect}
                sx={{ py: 1.5, fontWeight: 700 }}
              >
                Redirect Now
              </Button>
              <Button
                component={RouterLink}
                to="/login"
                variant="text"
                color="inherit"
                size="small"
                sx={{ fontWeight: 600 }}
              >
                Back to Sign In
              </Button>
            </Stack>
          </Stack>
        </EnterpriseCard>
      </Box>
    </Box>
  )
}
