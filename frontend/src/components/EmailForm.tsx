import { EmailOutlined } from '@mui/icons-material'
import { Button, Stack, TextField } from '@mui/material'
import type { FormEvent } from 'react'

interface EmailFormProps {
  email: string
  isSubmitting: boolean
  onEmailChange: (email: string) => void
  onSubmit: () => void
}

export function EmailForm({ email, isSubmitting, onEmailChange, onSubmit }: EmailFormProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit()
  }

  return (
    <Stack component="form" spacing={2} onSubmit={handleSubmit} noValidate>
      <TextField
        autoComplete="email"
        autoFocus
        fullWidth
        id="email"
        label="Email address"
        onChange={(event) => onEmailChange(event.target.value)}
        required
        type="email"
        value={email}
      />
      <Button disabled={isSubmitting || !email.trim()} size="large" startIcon={<EmailOutlined />} type="submit" variant="contained">
        {isSubmitting ? 'Sending code…' : 'Send OTP'}
      </Button>
    </Stack>
  )
}
