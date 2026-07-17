import { Box, Typography } from '@mui/material'
import { CheckCircleOutlined } from '@mui/icons-material'

interface ProgressStepperProps {
  step: number
  labels: string[]
}

export function ProgressStepper({ step, labels }: ProgressStepperProps) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
      {labels.map((label, index) => {
        const completed = step > index
        return (
          <Box key={label} sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 130 }}>
            <Box sx={{ width: 28, height: 28, borderRadius: '50%', bgcolor: completed ? 'primary.main' : 'divider', color: completed ? 'common.white' : 'text.secondary', display: 'grid', placeItems: 'center' }}>
              {completed ? <CheckCircleOutlined fontSize="small" /> : index + 1}
            </Box>
            <Typography sx={{ fontWeight: completed ? 700 : 500, color: completed ? 'text.primary' : 'text.secondary', fontSize: 14 }}>
              {label}
            </Typography>
          </Box>
        )
      })}
    </Box>
  )
}
