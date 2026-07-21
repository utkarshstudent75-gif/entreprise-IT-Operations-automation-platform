import { Box, Typography, Breadcrumbs, Link } from '@mui/material'
import { NavigateNextRounded } from '@mui/icons-material'
import { Link as RouterLink } from 'react-router-dom'

interface HeaderProps {
  title: string
  subtitle?: string
  breadcrumbs?: Array<{ label: string; path?: string }>
}

export function Header({ title, subtitle, breadcrumbs }: Readonly<HeaderProps>) {
  return (
    <Box sx={{ mb: 4 }}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumbs
          separator={<NavigateNextRounded sx={{ fontSize: 16 }} />}
          aria-label="breadcrumb"
          sx={{ mb: 1.5 }}
        >
          <Link
            component={RouterLink}
            underline="hover"
            color="inherit"
            to="/dashboard"
            sx={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center' }}
          >
            Portal
          </Link>
          {breadcrumbs.map((crumb, idx) => {
            const isLast = idx === breadcrumbs.length - 1
            return isLast || !crumb.path ? (
              <Typography
                key={crumb.label}
                color="text.primary"
                sx={{ fontSize: '0.8rem', fontWeight: 500 }}
              >
                {crumb.label}
              </Typography>
            ) : (
              <Link
                key={crumb.label}
                component={RouterLink}
                underline="hover"
                color="inherit"
                to={crumb.path}
                sx={{ fontSize: '0.8rem' }}
              >
                {crumb.label}
              </Link>
            )
          })}
        </Breadcrumbs>
      )}

      <Typography variant="h4" component="h1" sx={{ fontWeight: 800, letterSpacing: '-0.02em', mb: 0.5 }}>
        {title}
      </Typography>
      {subtitle && (
        <Typography variant="body1" color="text.secondary">
          {subtitle}
        </Typography>
      )}
    </Box>
  )
}
