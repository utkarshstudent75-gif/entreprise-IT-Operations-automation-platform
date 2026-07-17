import { AppBar, Box, Button, Toolbar, Typography } from '@mui/material'
import { NavLink } from 'react-router-dom'

const navLinks = [
  { label: 'Password Reset', path: '/' },
  { label: 'Create User', path: '/admin/create-user' },
]

export function NavigationBar() {
  return (
    <AppBar position="sticky" color="inherit" elevation={1} sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, md: 4 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ width: 42, height: 42, borderRadius: 1.5, bgcolor: 'primary.main', display: 'grid', placeItems: 'center' }}>
            <Typography variant="h6" sx={{ color: 'common.white', letterSpacing: 0.5 }}>
              E
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Enterprise IT Operations Platform
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Password reset and administration
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
          {navLinks.map((link) => (
            <Button
              key={link.path}
              component={NavLink}
              to={link.path}
              end
              size="small"
              sx={{
                borderRadius: 2,
                textTransform: 'none',
                color: 'text.primary',
                '&.active': {
                  bgcolor: 'primary.main',
                  color: 'common.white',
                },
              }}
            >
              {link.label}
            </Button>
          ))}
        </Box>
      </Toolbar>
    </AppBar>
  )
}
