import { Box, Container, IconButton, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText } from '@mui/material'
import { MenuRounded, DashboardRounded } from '@mui/icons-material'
import { useState } from 'react'
import type { ReactNode } from 'react'
import { Navbar } from '../components/Navbar'
import { Sidebar } from '../components/Sidebar'

interface DashboardLayoutProps {
  children: ReactNode
}

export function DashboardLayout({ children }: Readonly<DashboardLayoutProps>) {
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: '#f4f6fb' }}>
      {/* Navbar */}
      <Navbar />

      {/* Main Container */}
      <Box sx={{ display: 'flex', flex: 1, position: 'relative' }}>
        {/* Sidebar for Desktop */}
        <Sidebar />

        {/* Hamburger Menu for Mobile */}
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={handleDrawerToggle}
          sx={{
            position: 'absolute',
            top: -52, // Place it nicely in navbar empty space on mobile
            left: 16,
            zIndex: 1300,
            display: { md: 'none' },
          }}
        >
          <MenuRounded />
        </IconButton>

        {/* Mobile Sidebar Drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 260 },
          }}
        >
          {/* We reuse the sidebar list content in mobile, simplified or same */}
          <Box onClick={handleDrawerToggle} sx={{ p: 2 }}>
            <Sidebar />
          </Box>
        </Drawer>

        {/* Main Content Area */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: { xs: 2, md: 4 },
            width: { md: 'calc(100% - 260px)' },
            ml: { md: '260px' }, // Offset for the fixed sidebar
          }}
        >
          <Container maxWidth="xl" sx={{ p: 0 }}>
            {children}
          </Container>
        </Box>
      </Box>
    </Box>
  )
}
