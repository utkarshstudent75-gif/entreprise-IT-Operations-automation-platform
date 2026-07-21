import { Box, Card, CardActionArea, CardContent, Typography, Chip } from '@mui/material'
import { ArrowForwardRounded } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

interface DashboardCardProps {
  title: string
  description: string
  path: string
  icon: React.ReactNode
  isPlaceholder?: boolean
}

export function DashboardCard({ title, description, path, icon, isPlaceholder = false }: Readonly<DashboardCardProps>) {
  const navigate = useNavigate()

  return (
    <Card
      elevation={0}
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 3,
        transition: 'transform 0.2s, box-shadow 0.2s, border-color 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 8px 24px rgba(21, 95, 193, 0.08)',
          borderColor: isPlaceholder ? 'divider' : 'primary.main',
        },
      }}
    >
      <CardActionArea onClick={() => navigate(path)} sx={{ height: '100%' }}>
        <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
          {/* Top row: Icon + status */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box
              sx={{
                width: 44,
                height: 44,
                borderRadius: 2,
                bgcolor: isPlaceholder ? 'action.hover' : 'primary.light',
                color: isPlaceholder ? 'text.secondary' : 'primary.contrastText',
                display: 'grid',
                placeItems: 'center',
              }}
            >
              {icon}
            </Box>
            <Chip
              label={isPlaceholder ? 'Coming Soon' : 'Active'}
              size="small"
              sx={{
                fontWeight: 600,
                fontSize: '0.7rem',
                bgcolor: isPlaceholder ? 'action.selected' : '#e6f4ea',
                color: isPlaceholder ? 'text.secondary' : '#137333',
              }}
            />
          </Box>

          {/* Title & Description */}
          <Box sx={{ flexGrow: 1, mb: 2 }}>
            <Typography variant="h6" component="h3" sx={{ fontWeight: 700, mb: 1, fontSize: '1.05rem' }}>
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ lineClamp: 2, overflow: 'hidden', display: '-webkit-box', WebkitBoxOrient: 'vertical', WebkitLineClamp: 2 }}>
              {description}
            </Typography>
          </Box>

          {/* Arrow footer */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: isPlaceholder ? 'text.disabled' : 'primary.main' }}>
            <Typography variant="caption" sx={{ fontWeight: 700 }}>
              {isPlaceholder ? 'View Details' : 'Launch Feature'}
            </Typography>
            <ArrowForwardRounded sx={{ fontSize: 14 }} />
          </Box>
        </CardContent>
      </CardActionArea>
    </Card>
  )
}
