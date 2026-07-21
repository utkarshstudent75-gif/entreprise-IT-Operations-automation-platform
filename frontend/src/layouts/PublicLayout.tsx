import { Box, Container, Typography } from '@mui/material'
import type { ReactNode } from 'react'

interface PublicLayoutProps {
  children: ReactNode
}

export function PublicLayout({ children }: Readonly<PublicLayoutProps>) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: '#f4f6fb',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Mini public header */}
      <Box
        component="header"
        sx={{
          py: 2,
          px: { xs: 2, md: 4 },
          bgcolor: 'common.white',
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          gap: 2,
        }}
      >
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: 1,
            bgcolor: 'primary.main',
            display: 'grid',
            placeItems: 'center',
          }}
        >
          <Typography variant="body1" sx={{ color: 'common.white', fontWeight: 800 }}>
            E
          </Typography>
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '1.1rem' }}>
          Enterprise IT Operations Portal
        </Typography>
      </Box>

      {/* Main body */}
      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', py: { xs: 3, md: 5 } }}>
        <Container maxWidth="md">
          {children}
        </Container>
      </Box>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 3,
          px: { xs: 2, md: 4 },
          bgcolor: 'common.white',
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Typography variant="body2" color="text.secondary" align="center">
          Enterprise IT Operations Portal — Version 1.0.0 — Powered by FastAPI + React
        </Typography>
      </Box>
    </Box>
  )
}
