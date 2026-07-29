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
  PersonRounded,
  NotificationsRounded,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'

const sidebarWidth = 260

interface SidebarItem {
  label: string
  path: string
  icon: React.ComponentType
  roles?: string[]
}

interface SidebarGroup {
  title: string
  items: SidebarItem[]
}

const sidebarGroups: SidebarGroup[] = [
  {
    title: 'User Center',
    items: [
      { label: 'My Profile', path: '/dashboard/profile', icon: PersonRounded },
      { label: 'Reset History', path: '/dashboard/reset-history', icon: HistoryRounded },
      { label: 'Session Information', path: '/dashboard/session-info', icon: VpnKeyRounded },
      { label: 'Notification Center', path: '/dashboard/notifications', icon: NotificationsRounded },
    ],
  },
  {
    title: 'Identity Services',
    items: [
      { label: 'Password Reset', path: '/dashboard/password-reset', icon: LockResetRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'MFA Reset', path: '/dashboard/mfa-reset', icon: VpnKeyRounded, roles: ['Platform Administrator', 'Support Engineer'] },
      { label: 'Unlock Account', path: '/dashboard/unlock-account', icon: LockOpenRounded, roles: ['Platform Administrator', 'Support Engineer'] },
    ],
  },
  {
    title: 'Software & Access',
    items: [
      { label: 'Software Request', path: '/dashboard/software-request', icon: AppShortcutRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'Access Request', path: '/dashboard/access-request', icon: VpnLockRounded, roles: ['Platform Administrator', 'Support Engineer'] },
      { label: 'License Assignment', path: '/dashboard/license-assignment', icon: AssignmentIndRounded, roles: ['Platform Administrator'] },
    ],
  },
  {
    title: 'Support',
    items: [
      { label: 'My Requests', path: '/dashboard/my-requests', icon: HistoryRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'My Tickets', path: '/dashboard/my-tickets', icon: SupportAgentRounded, roles: ['Platform Administrator', 'Support Engineer'] },
      { label: 'AI Assistant', path: '/dashboard/ai-assistant', icon: SmartToyRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
    ],
  },
  {
    title: 'Administration',
    items: [
      { label: 'Admin Dashboard', path: '/dashboard/admin', icon: ShieldRounded, roles: ['Platform Administrator'] },
    ],
  },
]

export function Sidebar() {
  const { user } = useAuth()
  
  if (!user) return null

  // Filter sidebar groups based on user role
  const filteredGroups = sidebarGroups
    .map((group) => {
      const filteredItems = group.items.filter(
        (item) => !item.roles || item.roles.includes(user.role)
      )
      return { ...group, items: filteredItems }
    })
    .filter((group) => group.items.length > 0)

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

          {filteredGroups.map((group) => (
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

