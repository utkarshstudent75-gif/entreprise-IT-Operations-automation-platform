import { Box } from '@mui/material'
import { AdminCreateUserPage } from '../AdminCreateUserPage'
import { Header } from '../../components/Header'

export function AdminDashboard() {
  return (
    <Box>
      <Header
        title="Admin Dashboard"
        breadcrumbs={[{ label: 'Administration' }]}
      />
      <AdminCreateUserPage />
    </Box>
  )
}
