import { Box, Card, List, ListItem, ListItemIcon, ListItemText, Typography, Stack } from '@mui/material'
import { CheckCircleRounded, InfoRounded, ShieldRounded, NotificationsRounded } from '@mui/icons-material'
import { useAuth } from '../../contexts/AuthContext'
import { Header } from '../../components/Header'

export function NotificationCenter() {
  const { user } = useAuth()

  // Generate some realistic security notifications
  const notifications = [
    {
      id: 1,
      title: 'Sign In Successful',
      description: `Successfully signed in using Microsoft Entra ID. Session privileges initialized for role: ${user?.role ?? 'Standard User'}.`,
      time: 'Just now',
      type: 'info',
      icon: InfoRounded,
    },
    {
      id: 2,
      title: 'MFA Registration Status Checked',
      description: 'System verified active Multi-Factor Authentication registrations inside Microsoft Security Info.',
      time: '15 minutes ago',
      type: 'success',
      icon: CheckCircleRounded,
    },
    {
      id: 3,
      title: 'Security Context Mapped',
      description: `Role based access groups successfully loaded. Verified access scope matches ${user?.role ?? 'Standard User'}.`,
      time: '1 hour ago',
      type: 'security',
      icon: ShieldRounded,
    },
  ]

  return (
    <Box>
      <Header
        title="Notification Center"
        subtitle="Review security events, access logs, and account alert history."
        breadcrumbs={[{ label: 'User Center' }, { label: 'Notification Center' }]}
      />

      <Card
        sx={{
          p: 4,
          mt: 3,
          borderRadius: 4,
          border: '1px solid',
          borderColor: 'divider',
          maxWidth: 900,
        }}
      >
        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 3 }}>
          <NotificationsRounded color="primary" />
          <Typography variant="h6" sx={{ fontWeight: 800 }}>
            Recent Security Actions
          </Typography>
        </Stack>

        <List>
          {notifications.map((item, index) => {
            const Icon = item.icon
            let color = 'info.main'
            if (item.type === 'success') {
              color = 'success.main'
            } else if (item.type === 'security') {
              color = 'error.main'
            }

            return (
              <ListItem 
                key={item.id} 
                alignItems="flex-start"
                sx={{ 
                  px: 2, 
                  py: 2,
                  mb: index < notifications.length - 1 ? 2 : 0,
                  borderRadius: 2,
                  border: '1px solid',
                  borderColor: 'divider',
                  bgcolor: 'background.paper',
                }}
              >
                <ListItemIcon sx={{ mt: 0.5 }}>
                  <Icon sx={{ color }} />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                        {item.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {item.time}
                      </Typography>
                    </Stack>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      {item.description}
                    </Typography>
                  }
                />
              </ListItem>
            )
          })}
        </List>
      </Card>
    </Box>
  )
}
