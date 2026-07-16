import { CheckCircleRounded, LockResetRounded, SecurityRounded } from '@mui/icons-material'
import { Box, Button, Container, Paper, Stack, Step, StepLabel, Stepper, Typography } from '@mui/material'
import { useState } from 'react'
import { requestPasswordReset, verifyOtp } from '../api/passwordApi'
import { EmailForm } from '../components/EmailForm'
import { OtpForm } from '../components/OtpForm'
import { StatusAlert, type AlertSeverity } from '../components/StatusAlert'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [isRequesting, setIsRequesting] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [message, setMessage] = useState('')
  const [severity, setSeverity] = useState<AlertSeverity>('info')
  const [step, setStep] = useState(0)

  const showStatus = (nextMessage: string, nextSeverity: AlertSeverity) => {
    setMessage(nextMessage)
    setSeverity(nextSeverity)
  }

  const handleRequestReset = async () => {
    setIsRequesting(true)
    setMessage('')
    try {
      const response = await requestPasswordReset(email.trim())
      showStatus(response.message, response.success ? 'success' : 'error')
      if (response.success) setStep(1)
    } finally {
      setIsRequesting(false)
    }
  }

  const handleVerifyOtp = async () => {
    setIsVerifying(true)
    setMessage('')
    try {
      const response = await verifyOtp(email.trim(), otp.trim())
      showStatus(response.message, response.success ? 'success' : 'error')
      if (response.success) setStep(2)
    } finally {
      setIsVerifying(false)
    }
  }

  const restart = () => {
    setEmail('')
    setOtp('')
    setMessage('')
    setStep(0)
  }

  return (
    <Box sx={{ alignItems: 'center', bgcolor: '#f5f8ff', display: 'flex', minHeight: '100vh', py: { xs: 2, md: 5 } }}>
      <Container maxWidth="md">
        <Paper
          elevation={0}
          sx={{ border: '1px solid', borderColor: '#dfe7f5', borderRadius: { xs: 3, md: 5 }, overflow: 'hidden' }}
        >
          <Box sx={{ display: 'grid', gridTemplateColumns: { md: '0.85fr 1.15fr' } }}>
            <Box sx={{ bgcolor: '#0b3a82', color: 'common.white', p: { xs: 3, sm: 5 }, position: 'relative' }}>
              <Stack spacing={4} sx={{ position: 'relative', zIndex: 1 }}>
                <Box>
                  <Box sx={{ alignItems: 'center', bgcolor: 'rgba(255,255,255,.14)', borderRadius: 2, display: 'inline-flex', p: 1.25 }}>
                    <LockResetRounded fontSize="large" />
                  </Box>
                  <Typography component="p" sx={{ fontSize: 13, fontWeight: 700, letterSpacing: 1.4, mt: 3, textTransform: 'uppercase' }}>
                    IT self service
                  </Typography>
                  <Typography component="h1" sx={{ fontSize: { xs: 30, sm: 36 }, fontWeight: 750, letterSpacing: '-.03em', lineHeight: 1.1, mt: 1 }}>
                    Reset your account password.
                  </Typography>
                  <Typography sx={{ color: 'rgba(255,255,255,.76)', lineHeight: 1.65, mt: 2 }}>
                    Verify your work email to securely begin your password-reset request.
                  </Typography>
                </Box>
                <Stack spacing={2.25}>
                  {['A time-limited verification code', 'Protected by enterprise security', 'No helpdesk ticket required'].map((item) => (
                    <Stack alignItems="center" direction="row" key={item} spacing={1.25}>
                      <CheckCircleRounded sx={{ color: '#8fc2ff', fontSize: 20 }} />
                      <Typography sx={{ fontSize: 14 }}>{item}</Typography>
                    </Stack>
                  ))}
                </Stack>
              </Stack>
              <SecurityRounded sx={{ bottom: -50, color: 'rgba(255,255,255,.06)', fontSize: 210, position: 'absolute', right: -45 }} />
            </Box>

            <Box sx={{ p: { xs: 3, sm: 5 } }}>
              <Typography color="primary" fontSize={13} fontWeight={800} letterSpacing={1.2} textTransform="uppercase">
                Account recovery
              </Typography>
              <Typography component="h2" sx={{ fontSize: { xs: 25, sm: 30 }, fontWeight: 750, letterSpacing: '-.025em', mt: 1 }}>
                {step === 0 ? 'Find your account' : step === 1 ? 'Enter your verification code' : 'You’re verified'}
              </Typography>
              <Typography color="text.secondary" sx={{ lineHeight: 1.6, mt: 1 }}>
                {step === 0 && 'Use the email address associated with your organization account.'}
                {step === 1 && `We sent a code to ${email}. Enter it below to continue.`}
                {step === 2 && 'Your identity has been confirmed. You can now continue with your password reset.'}
              </Typography>

              <Stepper activeStep={step} alternativeLabel sx={{ mt: 4, mb: 4 }}>
                {['Email', 'Verify', 'Complete'].map((label) => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
              </Stepper>

              {step === 0 && <EmailForm email={email} isSubmitting={isRequesting} onEmailChange={setEmail} onSubmit={handleRequestReset} />}
              {step === 1 && (
                <Stack spacing={2.5}>
                  <OtpForm email={email} isSubmitting={isVerifying} otp={otp} onOtpChange={setOtp} onSubmit={handleVerifyOtp} />
                  <Button onClick={() => setStep(0)} size="small" sx={{ alignSelf: 'flex-start', px: 0 }}>
                    Use a different email address
                  </Button>
                </Stack>
              )}
              {step === 2 && <Button fullWidth onClick={restart} size="large" variant="outlined">Start another request</Button>}
              <StatusAlert message={message} severity={severity} />
            </Box>
          </Box>
        </Paper>
        <Typography align="center" color="text.secondary" sx={{ fontSize: 13, mt: 2.5 }}>
          Enterprise IT Operations Automation Platform
        </Typography>
      </Container>
    </Box>
  )
}
