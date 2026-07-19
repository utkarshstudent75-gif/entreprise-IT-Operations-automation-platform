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

export function OtpForm({ email, isSubmitting, otp, onOtpChange, onSubmit }: Readonly<OtpFormProps>) {
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
        inputProps={{ inputMode: 'numeric', maxLength: 6, pattern: '[0-9]*' }}
        label="Six-digit verification code"
        onChange={(event) => onOtpChange(event.target.value.replace(/\D/g, ''))}
        placeholder="000000"
        required
        value={otp}
        sx={{ '& input': { fontSize: 22, fontWeight: 700, letterSpacing: 5, textAlign: 'center' } }}
      />
      <Button
        disabled={isSubmitting || !email.trim() || otp.length !== 6}
        size="large"
        startIcon={isSubmitting ? <CircularProgress color="inherit" size={20} /> : <VerifiedOutlined />}
        type="submit"
        variant="outlined"
      >
        {isSubmitting ? 'Verifying…' : 'Verify and continue'}
      </Button>
    </Stack>
  )
}
