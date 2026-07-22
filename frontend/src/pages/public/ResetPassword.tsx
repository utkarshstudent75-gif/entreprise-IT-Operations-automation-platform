import { Box, Stack, Typography, Button } from '@mui/material'
import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useSearchParams, Link as RouterLink } from 'react-router-dom'

import { resetPassword } from '../../api/passwordApi'
import { EnterpriseCard } from '../../components/EnterpriseCard'
import { FormAlert } from '../../components/FormAlert'
import { LoadingButton } from '../../components/LoadingButton'
import { PasswordInput } from '../../components/PasswordInput'
import { ProgressStepper } from '../../components/ProgressStepper'
import { TextInput } from '../../components/TextInput'

const stepLabels = ['Forgot Password', 'Verify OTP', 'Reset Password']

export function ResetPassword() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [statusSeverity, setStatusSeverity] = useState<'success' | 'error' | 'info'>('info')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const emailParam = searchParams.get('email')
    const otpParam = searchParams.get('otp')
    if (emailParam) setEmail(emailParam)
    if (otpParam) setOtp(otpParam)
  }, [searchParams])

  const canSubmitPassword = newPassword.length >= 8

  const passwordStrength = useMemo(() => {
    if (newPassword.length >= 12 && /[A-Z]/.test(newPassword) && /\d/.test(newPassword) && /[^A-Za-z0-9]/.test(newPassword)) {
      return 'Strong'
    }
    if (newPassword.length >= 10) {
      return 'Moderate'
    }
    return 'Weak'
  }, [newPassword])

  const handleResetPassword = async () => {
    setStatusMessage('')
    setStatusSeverity('info')
    setLoading(true)
    try {
      const response = await resetPassword(email.trim(), otp.trim(), newPassword)
      if (response.success) {
        setStatusMessage(response.message)
        setStatusSeverity('success')
        setTimeout(() => {
          navigate('/login')
        }, 2000)
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
          Reset Password
        </Typography>

        <Box sx={{ mb: 4 }}>
          <ProgressStepper step={3} labels={stepLabels} />
        </Box>

        <EnterpriseCard>
          <Stack spacing={3}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {stepLabels[2]}
            </Typography>

            <FormAlert open={Boolean(statusMessage)} severity={statusSeverity}>
              {statusMessage}
            </FormAlert>

            {statusSeverity === 'success' ? (
              <Stack spacing={2} sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="body1" color="text.secondary">
                  Your password has been successfully updated. You can now use your new password to sign in.
                </Typography>
                <Button component={RouterLink} to="/login" variant="contained" color="primary" sx={{ mt: 2 }}>
                  Go to Sign In
                </Button>
              </Stack>
            ) : (
              <Stack spacing={2}>
                <TextInput
                  label="Email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  helperText="Confirm the email for this password reset request."
                  type="email"
                />
                <TextInput
                  label="Verification code"
                  value={otp}
                  onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                  helperText="Enter the code you received by email."
                  inputProps={{ inputMode: 'numeric', maxLength: 6 }}
                />
                <PasswordInput
                  label="New password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  helperText={`Password strength: ${passwordStrength}`}
                  autoFocus
                />
                <LoadingButton variant="contained" loading={loading} onClick={handleResetPassword} disabled={!canSubmitPassword}>
                  Reset password
                </LoadingButton>
              </Stack>
            )}

            {statusSeverity !== 'success' && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                <Button component={RouterLink} to="/verify-otp" variant="text" size="small">
                  Back
                </Button>
                <Button component={RouterLink} to="/login" variant="text" size="small">
                  Back to Sign In
                </Button>
              </Box>
            )}
          </Stack>
        </EnterpriseCard>
      </Box>
    </Box>
  )
}
