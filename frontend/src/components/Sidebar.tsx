import { NavLink, useNavigate } from 'react-router-dom'
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
  ShieldRounded,
  PersonRounded,
  NotificationsRounded,
  LogoutRounded,
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
    title: 'Identity',
    items: [
      { label: 'Password Reset', path: '/dashboard/password-reset', icon: LockResetRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'MFA Management', path: '/dashboard/mfa-management', icon: VpnKeyRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'Reset MFA Methods', path: '/dashboard/mfa-reset', icon: VpnKeyRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'Unlock Account', path: '/dashboard/unlock-account', icon: LockOpenRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'My Profile', path: '/dashboard/profile', icon: PersonRounded },
      { label: 'Session Information', path: '/dashboard/session-info', icon: VpnKeyRounded },
    ],
  },
  {
    title: 'Requests',
    items: [
      { label: 'Software Request', path: '/dashboard/software-request', icon: AppShortcutRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'Software Approvals', path: '/dashboard/software-approvals', icon: AppShortcutRounded, roles: ['Platform Administrator', 'Support Engineer'] },
      { label: 'VPN Request', path: '/dashboard/vpn-request', icon: VpnLockRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'Shared Mailbox', path: '/dashboard/mailbox-request', icon: AppShortcutRounded, roles: ['Platform Administrator', 'Support Engineer', 'Standard User'] },
      { label: 'Access Request', path: '/dashboard/access-request', icon: VpnLockRounded, roles: ['Platform Administrator', 'Support Engineer'] },
      { label: 'License Assignment', path: '/dashboard/license-assignment', icon: AssignmentIndRounded, roles: ['Platform Administrator'] },
    ],
  },
  {
    title: 'System',
    items: [
      { label: 'Notifications', path: '/dashboard/notifications', icon: NotificationsRounded },
      { label: 'Reset History', path: '/dashboard/reset-history', icon: HistoryRounded },
      { label: 'Settings', path: '/dashboard/settings', icon: ShieldRounded },
      { label: 'Help', path: '/dashboard/help', icon: SupportAgentRounded },
    ],
  },
]

export function Sidebar() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  
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

          {/* Logout Button */}
          <ListItem disablePadding sx={{ mt: 3, borderTop: '1px solid', borderColor: 'divider', pt: 2 }}>
            <ListItemButton
              onClick={async () => {
                await logout()
                navigate('/')
              }}
              sx={{
                borderRadius: 2,
                py: 0.75,
                px: 2,
                color: 'error.main',
                '&:hover': {
                  bgcolor: '#ffebee',
                }
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: 'error.main' }}>
                <LogoutRounded />
              </ListItemIcon>
              <ListItemText
                primary="Sign Out"
                primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: 600 }}
              />
            </ListItemButton>
          </ListItem>
        </List>
      </Box>
    </Drawer>
  )
}
