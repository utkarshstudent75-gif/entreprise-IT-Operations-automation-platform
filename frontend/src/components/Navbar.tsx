import { AppBar, Box, Button, Toolbar, Typography, Chip, Avatar, Tooltip } from '@mui/material'
import { LogoutRounded, FiberManualRecordRounded } from '@mui/icons-material'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export function Navbar() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  // Determine role colors
  let roleColor: 'primary' | 'secondary' | 'error' | 'success' | 'warning' | 'info' = 'primary'
  if (user?.role === 'Platform Administrator') {
    roleColor = 'error'
  } else if (user?.role === 'Support Engineer') {
    roleColor = 'warning'
  } else if (user?.role === 'Auditor') {
    roleColor = 'success'
  }

  return (
    <AppBar position="sticky" color="inherit" elevation={1} sx={{ borderBottom: 1, borderColor: 'divider', zIndex: 1201 }}>
      <Toolbar sx={{ justifyContent: 'space-between', px: { xs: 2, md: 4 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Logo */}
          <Box
            sx={{
              width: 38,
              height: 38,
              borderRadius: 1.5,
              bgcolor: '#107c41', // Azure-style corporate color or primary
              display: 'grid',
              placeItems: 'center',
            }}
          >
            <Typography variant="h6" sx={{ color: 'common.white', fontWeight: 800 }}>
              E
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              Enterprise IT Operations Portal
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Self-Service Hub
            </Typography>
          </Box>
        </Box>
 
        {/* Action Panel */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {/* System status placeholder */}
          <Chip
            icon={<FiberManualRecordRounded sx={{ color: '#107c41 !important', fontSize: '12px !important' }} />}
            label="All systems operational"
            variant="outlined"
            size="small"
            sx={{
              borderColor: '#107c41',
              color: '#107c41',
              fontWeight: 600,
              bgcolor: '#f3faf5',
              display: { xs: 'none', sm: 'inline-flex' },
            }}
          />

          {user && (
            <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mr: 1 }}>
              <Tooltip title="View Profile">
                <Avatar 
                  component={RouterLink}
                  to="/dashboard/profile"
                  sx={{ 
                    width: 32, 
                    height: 32, 
                    fontSize: '0.85rem', 
                    bgcolor: 'primary.main',
                    cursor: 'pointer',
                    textDecoration: 'none',
                    color: 'common.white',
                  }}
                >
                  {user.name.charAt(0).toUpperCase()}
                </Avatar>
              </Tooltip>
              <Box sx={{ display: { xs: 'none', md: 'block' } }}>
                <Typography variant="caption" sx={{ fontWeight: 700, display: 'block', lineHeight: 1 }}>
                  {user.name}
                </Typography>
                <Chip 
                  label={user.role} 
                  size="small" 
                  color={roleColor}
                  sx={{ 
                    height: 16, 
                    fontSize: '0.65rem', 
                    fontWeight: 700,
                    borderRadius: 1, 
                    mt: 0.5,
                    px: 0.5,
                    '& .MuiChip-label': { px: 0.5 }
                  }} 
                />
              </Box>
            </Stack>
          )}

          <Button
            variant="outlined"
            color="inherit"
            startIcon={<LogoutRounded />}
            onClick={handleLogout}
            size="small"
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              fontSize: '0.85rem',
            }}
          >
            Sign Out
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  )
}
import { Stack } from '@mui/material'

