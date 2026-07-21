import { Box, Stack, Typography, Button } from '@mui/material'
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link as RouterLink } from 'react-router-dom'

import { verifyOtp } from '../../api/passwordApi'
import { EnterpriseCard } from '../../components/EnterpriseCard'
import { FormAlert } from '../../components/FormAlert'
import { LoadingButton } from '../../components/LoadingButton'
import { ProgressStepper } from '../../components/ProgressStepper'
import { TextInput } from '../../components/TextInput'

const stepLabels = ['Forgot Password', 'Verify OTP', 'Reset Password']

export function VerifyOTP() {
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [statusSeverity, setStatusSeverity] = useState<'success' | 'error' | 'info'>('info')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const emailParam = searchParams.get('email')
    if (emailParam) {
      setEmail(emailParam)
    }
  }, [searchParams])

  const canSubmitOtp = otp.trim().length === 6

  const handleVerifyOtp = async () => {
    setStatusMessage('')
    setStatusSeverity('info')
    setLoading(true)
    try {
      const response = await verifyOtp(email.trim(), otp.trim())
      if (response.success) {
        setStatusMessage(response.message)
        setStatusSeverity('success')
        setTimeout(() => {
          navigate(`/reset-password?email=${encodeURIComponent(email.trim())}&otp=${encodeURIComponent(otp.trim())}`)
        }, 1500)
      } else {
        setStatusMessage(response.message)
        setStatusSeverity('error')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
      <Box sx={{ width: '100%', maxWidth: 600 }}>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
          Verify OTP
        </Typography>

        <Box sx={{ mb: 4 }}>
          <ProgressStepper step={2} labels={stepLabels} />
        </Box>

        <EnterpriseCard>
          <Stack spacing={3}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {stepLabels[1]}
            </Typography>

            <FormAlert open={Boolean(statusMessage)} severity={statusSeverity}>
              {statusMessage}
            </FormAlert>

            <Stack spacing={2}>
              <TextInput
                label="Email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                helperText="Confirm the email used for the OTP code."
                type="email"
              />
              <TextInput
                label="Verification code"
                value={otp}
                onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                helperText="Enter the 6-digit code sent to your email."
                inputProps={{ inputMode: 'numeric', maxLength: 6 }}
                autoFocus
              />
              <LoadingButton variant="contained" loading={loading} onClick={handleVerifyOtp} disabled={!canSubmitOtp}>
                Verify OTP
              </LoadingButton>
            </Stack>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Button component={RouterLink} to="/password-reset" variant="text" size="small">
                Back
              </Button>
              <Button component={RouterLink} to="/login" variant="text" size="small">
                Back to Sign In
              </Button>
            </Box>
          </Stack>
        </EnterpriseCard>
      </Box>
    </Box>
  )
}
