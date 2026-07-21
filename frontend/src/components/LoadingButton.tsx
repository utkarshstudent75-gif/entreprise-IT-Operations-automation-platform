import { Button, CircularProgress } from '@mui/material'
import type { ButtonProps } from '@mui/material'

interface LoadingButtonProps extends ButtonProps {
  loading?: boolean
}

export function LoadingButton({ loading = false, children, disabled, ...props }: Readonly<LoadingButtonProps>) {
  return (
    <Button disabled={disabled || loading} {...props}>
      {loading ? <CircularProgress size={20} color="inherit" /> : children}
    </Button>
  )
}
