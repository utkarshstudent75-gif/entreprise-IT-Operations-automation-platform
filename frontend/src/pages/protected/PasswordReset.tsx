import { Box } from '@mui/material'
import { PasswordReset } from '../public/PasswordReset'
import { Header } from '../../components/Header'

export function ProtectedPasswordReset() {
  return (
    <Box>
      <Header
        title="Password Reset Service"
        breadcrumbs={[{ label: 'Password Reset' }]}
      />
      <PasswordReset />
    </Box>
  )
}

