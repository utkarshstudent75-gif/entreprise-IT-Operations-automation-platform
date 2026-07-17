import { IconButton, InputAdornment, TextField } from '@mui/material'
import { Visibility, VisibilityOff } from '@mui/icons-material'
import { useState } from 'react'
import type { TextFieldProps } from '@mui/material'

interface PasswordInputProps extends Omit<TextFieldProps, 'type'> {
  helperText?: string
}

export function PasswordInput({ helperText, ...props }: PasswordInputProps) {
  const [visible, setVisible] = useState(false)

  return (
    <TextField
      {...props}
      type={visible ? 'text' : 'password'}
      helperText={helperText}
      InputProps={{
        endAdornment: (
          <InputAdornment position="end">
            <IconButton onClick={() => setVisible((prev) => !prev)} edge="end">
              {visible ? <VisibilityOff /> : <Visibility />}
            </IconButton>
          </InputAdornment>
        ),
        ...props.InputProps,
      }}
    />
  )
}
