import { NavLink } from 'react-router-dom'
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Typography,
} from '@mui/material'
import {
  DashboardRounded,
  LockResetRounded,
  VpnKeyRounded,
  LockOpenRounded,
  AppShortcutRounded,
  VpnLockRounded,
  AssignmentIndRounded,
  HistoryRounded,
  SupportAgentRounded,
  SmartToyRounded,
  ShieldRounded,
} from '@mui/icons-material'

const sidebarWidth = 260

interface SidebarItem {
  label: string
  path: string
  icon: React.ComponentType
}

interface SidebarGroup {
  title: string
  items: SidebarItem[]
}

const sidebarGroups: SidebarGroup[] = [
  {
    title: 'Identity Services',
    items: [
      { label: 'Password Reset', path: '/dashboard/password-reset', icon: LockResetRounded },
      { label: 'MFA Reset', path: '/dashboard/mfa-reset', icon: VpnKeyRounded },
      { label: 'Unlock Account', path: '/dashboard/unlock-account', icon: LockOpenRounded },
    ],
  },
  {
    title: 'Software & Access',
    items: [
      { label: 'Software Request', path: '/dashboard/software-request', icon: AppShortcutRounded },
      { label: 'Access Request', path: '/dashboard/access-request', icon: VpnLockRounded },
      { label: 'License Assignment', path: '/dashboard/license-assignment', icon: AssignmentIndRounded },
    ],
  },
  {
    title: 'Support',
    items: [
      { label: 'My Requests', path: '/dashboard/my-requests', icon: HistoryRounded },
      { label: 'My Tickets', path: '/dashboard/my-tickets', icon: SupportAgentRounded },
      { label: 'AI Assistant', path: '/dashboard/ai-assistant', icon: SmartToyRounded },
    ],
  },
  {
    title: 'Administration',
    items: [
      { label: 'Admin Dashboard', path: '/dashboard/admin', icon: ShieldRounded },
    ],
  },
]

export function Sidebar() {
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: sidebarWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: sidebarWidth,
          boxSizing: 'border-box',
          bgcolor: '#fafbfc',
          borderRight: 1,
          borderColor: 'divider',
          top: '64px', // Height of standard AppBar
          height: 'calc(100vh - 64px)',
        },
        display: { xs: 'none', md: 'block' },
      }}
    >
      <Box sx={{ overflow: 'auto', py: 2 }}>
        <List sx={{ px: 1 }}>
          <ListItem disablePadding sx={{ mb: 2 }}>
            <ListItemButton
              component={NavLink}
              to="/dashboard"
              end
              sx={{
                borderRadius: 2,
                '&.active': {
                  bgcolor: 'primary.main',
                  color: 'common.white',
                  '& .MuiListItemIcon-root': { color: 'common.white' },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <DashboardRounded />
              </ListItemIcon>
              <ListItemText
                primary="Dashboard Home"
                primaryTypographyProps={{ fontSize: '0.9rem', fontWeight: 600 }}
              />
            </ListItemButton>
          </ListItem>

          {sidebarGroups.map((group) => (
            <Box key={group.title} sx={{ mb: 2 }}>
              <ListSubheader
                sx={{
                  bgcolor: 'transparent',
                  lineHeight: '24px',
                  fontWeight: 700,
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  color: 'text.secondary',
                  mb: 0.5,
                  px: 2,
                }}
              >
                {group.title}
              </ListSubheader>
              {group.items.map((item) => (
                <ListItem disablePadding key={item.label} sx={{ mb: 0.5 }}>
                  <ListItemButton
                    component={NavLink}
                    to={item.path}
                    sx={{
                      borderRadius: 2,
                      py: 0.75,
                      px: 2,
                      color: 'text.primary',
                      '&.active': {
                        bgcolor: 'primary.light',
                        color: 'primary.contrastText',
                        '& .MuiListItemIcon-root': { color: 'primary.contrastText' },
                      },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36, color: 'text.secondary' }}>
                      <item.icon />
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: 500 }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </Box>
          ))}
        </List>
      </Box>
    </Drawer>
  )
}
