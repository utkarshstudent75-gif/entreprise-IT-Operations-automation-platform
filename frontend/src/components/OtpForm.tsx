import { VerifiedOutlined } from '@mui/icons-material'
import { Button, CircularProgress, Stack, TextField } from '@mui/material'
import type { FormEvent } from 'react'

interface OtpFormProps {
  email: string
  isSubmitting: boolean
  otp: string
  onOtpChange: (otp: string) => void
  onSubmit: () => void
}

export function OtpForm({ email, isSubmitting, otp, onOtpChange, onSubmit }: OtpFormProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit()
  }

  return (
    <Stack component="form" spacing={2} onSubmit={handleSubmit} noValidate>
      <TextField
        autoComplete="one-time-code"
        fullWidth
        helperText={email ? `Code sent for ${email}` : 'Enter your email address first.'}
        id="otp"
        inputProps={{ inputMode: 'numeric', maxLength: 8 }}
        label="One-time password"
        onChange={(event) => onOtpChange(event.target.value)}
        placeholder="Enter verification code"
        required
        value={otp}
      />
      <Button
        disabled={isSubmitting || !email.trim() || !otp.trim()}
        size="large"
        startIcon={isSubmitting ? <CircularProgress color="inherit" size={20} /> : <VerifiedOutlined />}
        type="submit"
        variant="outlined"
      >
        {isSubmitting ? 'Verifying…' : 'Verify OTP'}
      </Button>
    </Stack>
  )
}
