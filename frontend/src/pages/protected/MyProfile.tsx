import { Box, Card, Stack, Typography, Avatar, Chip, Grid, Divider } from '@mui/material'
import { AccountBoxRounded, ShieldRounded, BadgeRounded, ContactMailRounded, CalendarMonthRounded } from '@mui/icons-material'
import { useAuth } from '../../contexts/AuthContext'
import { Header } from '../../components/Header'

export function MyProfile() {
  const { user } = useAuth()

  if (!user) return null

  // Determine role colors
  let roleColor: 'primary' | 'secondary' | 'error' | 'success' | 'warning' | 'info' = 'primary'
  if (user.role === 'Platform Administrator') {
    roleColor = 'error'
  } else if (user.role === 'Support Engineer') {
    roleColor = 'warning'
  } else if (user.role === 'Auditor') {
    roleColor = 'success'
  }

  return (
    <Box>
      <Header
        title="My Profile"
        subtitle="View and manage your identity credentials and security details."
        breadcrumbs={[{ label: 'User Center' }, { label: 'My Profile' }]}
      />

      <Grid container spacing={3} sx={{ mt: 2, maxWidth: 900 }}>
        {/* Profile Card */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card
            sx={{
              p: 4,
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
            <Avatar
              sx={{
                width: 96,
                height: 96,
                fontSize: '2.5rem',
                bgcolor: 'primary.main',
                mb: 2,
                boxShadow: '0 4px 12px rgba(21, 95, 193, 0.2)',
              }}
            >
              {user.name.charAt(0).toUpperCase()}
            </Avatar>
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
              {user.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {user.email}
            </Typography>
            <Chip
              label={user.role}
              color={roleColor}
              size="small"
              icon={<ShieldRounded />}
              sx={{ fontWeight: 700, borderRadius: 2 }}
            />
          </Card>
        </Grid>

        {/* Account Details */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card
            sx={{
              p: 4,
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
            }}
          >
            <Typography variant="h6" sx={{ fontWeight: 800, mb: 3 }}>
              Account Information
            </Typography>

            <Stack spacing={2.5}>
              <Stack direction="row" spacing={2} alignItems="center">
                <BadgeRounded color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textTransform: 'uppercase', fontWeight: 700, fontSize: '0.65rem' }}>
                    Full Name
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {user.name}
                  </Typography>
                </Box>
              </Stack>
              
              <Divider />

              <Stack direction="row" spacing={2} alignItems="center">
                <ContactMailRounded color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textTransform: 'uppercase', fontWeight: 700, fontSize: '0.65rem' }}>
                    User Principal Name (UPN) / Email
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {user.email}
                  </Typography>
                </Box>
              </Stack>
              
              <Divider />

              <Stack direction="row" spacing={2} alignItems="center">
                <AccountBoxRounded color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textTransform: 'uppercase', fontWeight: 700, fontSize: '0.65rem' }}>
                    Security Privilege Group
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {user.role}
                  </Typography>
                </Box>
              </Stack>
              
              <Divider />

              <Stack direction="row" spacing={2} alignItems="center">
                <CalendarMonthRounded color="action" />
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textTransform: 'uppercase', fontWeight: 700, fontSize: '0.65rem' }}>
                    Account Status
                  </Typography>
                  <Typography variant="body1" color="success.main" sx={{ fontWeight: 700 }}>
                    Active (Synchronized with Entra ID)
                  </Typography>
                </Box>
              </Stack>
            </Stack>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
