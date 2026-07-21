import { Alert, Collapse } from '@mui/material'
import type { ReactNode } from 'react'

interface FormAlertProps {
  children: ReactNode
  severity: 'success' | 'error' | 'info' | 'warning'
  open: boolean
}

export function FormAlert({ children, severity, open }: Readonly<FormAlertProps>) {
  return (
    <Collapse in={open} appear>
      <Alert severity={severity} sx={{ mt: 2 }}>
        {children}
      </Alert>
    </Collapse>
  )
}
