import { Paper } from '@mui/material'
import type { ReactNode } from 'react'

interface EnterpriseCardProps {
  children: ReactNode
}

export function EnterpriseCard({ children }: EnterpriseCardProps) {
  return (
    <Paper elevation={2} sx={{ borderRadius: 3, p: { xs: 3, md: 4 }, bgcolor: 'background.paper', boxShadow: '0 10px 30px rgba(15, 23, 42, 0.06)' }}>
      {children}
    </Paper>
  )
}
