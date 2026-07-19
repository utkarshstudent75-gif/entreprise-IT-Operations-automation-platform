import { Box, Container, Typography } from '@mui/material'
import type { ReactNode } from 'react'
import { NavigationBar } from './NavigationBar'

interface ContentShellProps {
  children: ReactNode
}

export function ContentShell({ children }: Readonly<ContentShellProps>) {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#f4f6fb' }}>
      <NavigationBar />
      <Container maxWidth="lg" sx={{ py: { xs: 3, md: 5 }, maxWidth: 1100 }}>
        {children}
      </Container>
      <Box component="footer" sx={{ py: 3, px: { xs: 2, md: 4 }, bgcolor: 'common.white', borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Enterprise Password Reset Platform — Version 1.0.0 — Powered by FastAPI + React
        </Typography>
      </Box>
    </Box>
  )
}
