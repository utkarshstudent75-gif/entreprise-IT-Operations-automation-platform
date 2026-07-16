import { EmailOutlined } from '@mui/icons-material'
import { Button, CircularProgress, InputAdornment, Stack, TextField, Typography } from '@mui/material'
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
        helperText="We’ll send a one-time verification code to this address."
        label="Work email address"
        onChange={(event) => onEmailChange(event.target.value)}
        required
        type="email"
        value={email}
        slotProps={{ input: { startAdornment: <InputAdornment position="start"><EmailOutlined fontSize="small" /></InputAdornment> } }}
      />
      <Button
        disabled={isSubmitting || !email.trim()}
        size="large"
        startIcon={isSubmitting ? <CircularProgress color="inherit" size={20} /> : <EmailOutlined />}
        type="submit"
        variant="contained"
      >
        {isSubmitting ? 'Sending code…' : 'Send verification code'}
      </Button>
      <Typography color="text.secondary" fontSize={12} lineHeight={1.5} textAlign="center">
        Only accounts registered in your organization can be verified.
      </Typography>
    </Stack>
  )
}
