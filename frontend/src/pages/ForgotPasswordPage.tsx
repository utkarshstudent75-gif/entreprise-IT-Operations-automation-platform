import { LockResetOutlined } from '@mui/icons-material'
import { Box, Container, Divider, Paper, Stack, Typography } from '@mui/material'
import axios from 'axios'
import { useState } from 'react'
import { requestPasswordReset, verifyOtp } from '../api/passwordApi'
import { EmailForm } from '../components/EmailForm'
import { OtpForm } from '../components/OtpForm'
import { StatusAlert, type AlertSeverity } from '../components/StatusAlert'

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError<{ detail?: string; message?: string }>(error)) {
    return error.response?.data?.detail ?? error.response?.data?.message ?? fallback
  }

  return fallback
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [isRequesting, setIsRequesting] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [message, setMessage] = useState('')
  const [severity, setSeverity] = useState<AlertSeverity>('info')

  const showStatus = (nextMessage: string, nextSeverity: AlertSeverity) => {
    setMessage(nextMessage)
    setSeverity(nextSeverity)
  }

  const handleRequestReset = async () => {
    setIsRequesting(true)
    setMessage('')
    try {
      const response = await requestPasswordReset(email.trim())
      showStatus(response.message, 'success')
    } catch (error) {
      showStatus(getErrorMessage(error, 'Unable to send an OTP. Please try again.'), 'error')
    } finally {
      setIsRequesting(false)
    }
  }

  const handleVerifyOtp = async () => {
    setIsVerifying(true)
    setMessage('')
    try {
      const response = await verifyOtp(email.trim(), otp.trim())
      showStatus(response.message, 'success')
    } catch (error) {
      showStatus(getErrorMessage(error, 'Unable to verify the OTP. Please try again.'), 'error')
    } finally {
      setIsVerifying(false)
    }
  }

  return (
    <Box sx={{ alignItems: 'center', bgcolor: 'grey.100', display: 'flex', minHeight: '100vh', py: 3 }}>
      <Container maxWidth="sm">
        <Paper elevation={0} sx={{ border: 1, borderColor: 'divider', borderRadius: 3, p: { xs: 3, sm: 4 } }}>
          <Stack spacing={3}>
            <Stack alignItems="center" spacing={1} textAlign="center">
              <LockResetOutlined color="primary" sx={{ fontSize: 40 }} />
              <Typography component="h1" variant="h4">IT Enterprise Automation Platform</Typography>
              <Typography color="text.secondary">Request and verify a password reset code.</Typography>
            </Stack>
            <EmailForm email={email} isSubmitting={isRequesting} onEmailChange={setEmail} onSubmit={handleRequestReset} />
            <Divider>Already have a code?</Divider>
            <OtpForm email={email} isSubmitting={isVerifying} otp={otp} onOtpChange={setOtp} onSubmit={handleVerifyOtp} />
          </Stack>
          <StatusAlert message={message} severity={severity} />
        </Paper>
      </Container>
    </Box>
  )
}
