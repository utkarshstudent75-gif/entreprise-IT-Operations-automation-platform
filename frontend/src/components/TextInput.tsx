import { TextField } from '@mui/material'
import type { TextFieldProps } from '@mui/material'

export function TextInput(props: TextFieldProps) {
  return <TextField fullWidth {...props} />
}
