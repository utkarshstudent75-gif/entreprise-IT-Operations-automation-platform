import { Box } from '@mui/material'
import { PasswordResetPage } from '../PasswordResetPage'
import { Header } from '../../components/Header'

export function ProtectedPasswordReset() {
  return (
    <Box>
      <Header
        title="Password Reset Service"
        breadcrumbs={[{ label: 'Password Reset' }]}
      />
      <PasswordResetPage />
    </Box>
  )
}
