import { Alert, Collapse } from '@mui/material'

export type AlertSeverity = 'error' | 'info' | 'success' | 'warning'

interface StatusAlertProps {
  message: string
  severity: AlertSeverity
}

export function StatusAlert({ message, severity }: StatusAlertProps) {
  return (
    <Collapse in={Boolean(message)}>
      <Alert severity={severity} sx={{ mt: 3 }}>
        {message}
      </Alert>
    </Collapse>
  )
}
