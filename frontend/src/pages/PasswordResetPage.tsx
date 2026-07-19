import { Box, Stack, Typography } from '@mui/material'
import { useMemo, useState } from 'react'

import { requestPasswordReset, resetPassword, verifyOtp } from '../api/passwordApi'
import { EnterpriseCard } from '../components/EnterpriseCard'
import { FormAlert } from '../components/FormAlert'
import { LoadingButton } from '../components/LoadingButton'
import { PasswordInput } from '../components/PasswordInput'
import { ProgressStepper } from '../components/ProgressStepper'
import { TextInput } from '../components/TextInput'

const stepLabels = ['Forgot Password', 'Verify OTP', 'Reset Password']

export function PasswordResetPage() {
  const [step, setStep] = useState(0)
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [statusSeverity, setStatusSeverity] = useState<'success' | 'error' | 'info'>('info')
  const [loading, setLoading] = useState(false)

  const canSubmitEmail = email.trim().length > 0
  const canSubmitOtp = otp.trim().length === 6
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

  const clearStatus = () => {
    setStatusMessage('')
    setStatusSeverity('info')
  }

  const handleRequestReset = async () => {
    clearStatus()
    setLoading(true)
    try {
      const response = await requestPasswordReset(email.trim())
      if (response.success) {
        setStep(1)
        setStatusMessage(response.message)
        setStatusSeverity('success')
      } else {
        setStatusMessage(response.message)
        setStatusSeverity('error')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOtp = async () => {
    clearStatus()
    setLoading(true)
    try {
      const response = await verifyOtp(email.trim(), otp.trim())
      if (response.success) {
        setStep(2)
        setStatusMessage(response.message)
        setStatusSeverity('success')
      } else {
        setStatusMessage(response.message)
        setStatusSeverity('error')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleResetPassword = async () => {
    clearStatus()
    setLoading(true)
    try {
      const response = await resetPassword(email.trim(), otp.trim(), newPassword)
      if (response.success) {
        setStatusMessage(response.message)
        setStatusSeverity('success')
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
      <Box sx={{ width: '100%', maxWidth: 900 }}>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
          Password Reset
        </Typography>

        <ProgressStepper step={step + 1} labels={stepLabels} />

        <EnterpriseCard>
          <Stack spacing={3}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {stepLabels[step]}
            </Typography>

            <FormAlert open={Boolean(statusMessage)} severity={statusSeverity}>
              {statusMessage}
            </FormAlert>

            {step === 0 && (
              <Stack spacing={2}>
                <TextInput
                  label="Work email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  helperText="Enter the email associated with your corporate account."
                  type="email"
                  autoFocus
                />
                <LoadingButton variant="contained" loading={loading} onClick={handleRequestReset} disabled={!canSubmitEmail}>
                  Send reset code
                </LoadingButton>
              </Stack>
            )}

            {step === 1 && (
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
                />
                <LoadingButton variant="contained" loading={loading} onClick={handleVerifyOtp} disabled={!canSubmitOtp}>
                  Verify OTP
                </LoadingButton>
              </Stack>
            )}

            {step === 2 && (
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
                />
                <LoadingButton variant="contained" loading={loading} onClick={handleResetPassword} disabled={!canSubmitPassword}>
                  Reset password
                </LoadingButton>
              </Stack>
            )}
          </Stack>
        </EnterpriseCard>
      </Box>
    </Box>
  )
}
