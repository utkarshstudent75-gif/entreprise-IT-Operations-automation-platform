import { Box, Stack, Typography, List, ListItem, ListItemIcon, ListItemText, LinearProgress } from '@mui/material'
import { useMemo, useState, useEffect } from 'react'
import { CheckCircleRounded, RadioButtonUncheckedRounded } from '@mui/icons-material'

import { useNavigate } from 'react-router-dom'

import { requestPasswordReset, resetPassword, verifyOtp, getPasswordPolicy, PasswordPolicy } from '../api/passwordApi'
import { EnterpriseCard } from '../components/EnterpriseCard'
import { FormAlert } from '../components/FormAlert'
import { LoadingButton } from '../components/LoadingButton'
import { PasswordInput } from '../components/PasswordInput'
import { ProgressStepper } from '../components/ProgressStepper'
import { TextInput } from '../components/TextInput'

const stepLabels = ['Forgot Password', 'Verify OTP', 'Reset Password']

export function PasswordResetPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [statusSeverity, setStatusSeverity] = useState<'success' | 'error' | 'info'>('info')
  const [loading, setLoading] = useState(false)
  const [policy, setPolicy] = useState<PasswordPolicy>({
    min_length: 12,
    require_uppercase: true,
    require_lowercase: true,
    require_numbers: true,
    require_special: true,
  })

  // Load password complexity policy from backend on mount
  useEffect(() => {
    const fetchPolicy = async () => {
      const activePolicy = await getPasswordPolicy()
      setPolicy(activePolicy)
    }
    fetchPolicy()
  }, [])

  // Complexity criteria checks
  const criteria = useMemo(() => {
    return {
      length: newPassword.length >= policy.min_length,
      uppercase: !policy.require_uppercase || /[A-Z]/.test(newPassword),
      lowercase: !policy.require_lowercase || /[a-z]/.test(newPassword),
      number: !policy.require_numbers || /\d/.test(newPassword),
      special: !policy.require_special || /[^A-Za-z0-9]/.test(newPassword),
    }
  }, [newPassword, policy])

  const canSubmitEmail = email.trim().length > 0
  const canSubmitOtp = otp.trim().length === 6
  
  const passwordsMatch = newPassword === confirmPassword
  
  // Submit only if ALL policy criteria are satisfied AND passwords match
  const canSubmitPassword = useMemo(() => {
    return Object.values(criteria).every(Boolean) && passwordsMatch && newPassword.length > 0
  }, [criteria, passwordsMatch, newPassword])

  const passwordStrength = useMemo(() => {
    const satisfiedCount = Object.values(criteria).filter(Boolean).length
    if (satisfiedCount === 5 && newPassword.length >= 14) {
      return 'Strong'
    }
    if (satisfiedCount >= 4) {
      return 'Moderate'
    }
    return 'Weak'
  }, [criteria, newPassword])

  const strengthColor = useMemo(() => {
    if (passwordStrength === 'Strong') return 'success'
    if (passwordStrength === 'Moderate') return 'warning'
    return 'error'
  }, [passwordStrength])
  
  const strengthValue = useMemo(() => {
    if (!newPassword) return 0
    const satisfiedCount = Object.values(criteria).filter(Boolean).length
    return satisfiedCount * 20
  }, [criteria, newPassword])

  const clearStatus = () => {
    setStatusMessage('')
    setStatusSeverity('info')
  }

  const handleRequestReset = async () => {
    clearStatus()
    setLoading(true)
    try {
      const response = await requestPasswordReset(email.trim())
      if (response.success) {
        setStep(1)
        setStatusMessage(response.message)
        setStatusSeverity('success')
      } else {
        setStatusMessage(response.message)
        setStatusSeverity('error')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOtp = async () => {
    clearStatus()
    setLoading(true)
    try {
      const response = await verifyOtp(email.trim(), otp.trim())
      if (response.success) {
        setStep(2)
        setStatusMessage(response.message)
        setStatusSeverity('success')
      } else {
        setStatusMessage(response.message)
        setStatusSeverity('error')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleResetPassword = async () => {
    clearStatus()
    setLoading(true)
    try {
      const response = await resetPassword(email.trim(), otp.trim(), newPassword, confirmPassword)
      if (response.success) {
        setStatusMessage(response.message)
        setStatusSeverity('success')
        setTimeout(() => {
          navigate('/login')
        }, 2000)
      } else {
        setStatusMessage(response.message)
        setStatusSeverity('error')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
      <Box sx={{ width: '100%', maxWidth: 900 }}>
        <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
          Password Reset
        </Typography>

        <ProgressStepper step={step + 1} labels={stepLabels} />

        <EnterpriseCard>
          <Stack spacing={3}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {stepLabels[step]}
            </Typography>

            <FormAlert open={Boolean(statusMessage)} severity={statusSeverity}>
              {statusMessage}
            </FormAlert>

            {step === 0 && (
              <Stack spacing={2}>
                <TextInput
                  label="Work email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  helperText="Enter the email associated with your corporate account."
                  type="email"
                  autoFocus
                />
                <LoadingButton variant="contained" loading={loading} onClick={handleRequestReset} disabled={!canSubmitEmail}>
                  Send reset code
                </LoadingButton>
              </Stack>
            )}

            {step === 1 && (
              <Stack spacing={2}>
                <TextInput
                  label="Email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  helperText="Confirm the email used for the OTP code."
                  type="email"
                />
                <TextInput
                  label="Verification code"
                  value={otp}
                  onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                  helperText="Enter the 6-digit code sent to the business phone number associated with your profile in Entra ID."
                  inputProps={{ inputMode: 'numeric', maxLength: 6 }}
                />
                <LoadingButton variant="contained" loading={loading} onClick={handleVerifyOtp} disabled={!canSubmitOtp}>
                  Verify OTP
                </LoadingButton>
              </Stack>
            )}

            {step === 2 && (
              <Stack spacing={2.5}>
                <TextInput
                  label="Email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  helperText="Confirm the email for this password reset request."
                  type="email"
                />
                <TextInput
                  label="Verification code"
                  value={otp}
                  onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                  helperText="Enter the 6-digit code sent to your business phone number in Entra ID."
                  inputProps={{ inputMode: 'numeric', maxLength: 6 }}
                />
                <PasswordInput
                  label="New password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                />

                <PasswordInput
                  label="Confirm new password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  error={Boolean(confirmPassword && !passwordsMatch)}
                  helperText={confirmPassword && !passwordsMatch ? "Passwords do not match." : ""}
                />

                {/* Visually outstanding password strength indicator */}
                <Box sx={{ mt: 1, mb: 1 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                      Password Strength: <span style={{ color: strengthColor === 'success' ? '#2e7d32' : strengthColor === 'warning' ? '#ed6c02' : '#d32f2f' }}>{newPassword ? passwordStrength : 'None'}</span>
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                      {strengthValue}%
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="determinate"
                    value={strengthValue}
                    color={strengthColor}
                    sx={{ height: 8, borderRadius: 4, bgcolor: '#e0e0e0' }}
                  />
                </Box>

                {/* Dynamic Password Policy Complexity Checklist */}
                <Box sx={{ p: 2, bgcolor: '#f4f6fb', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1, color: 'text.primary' }}>
                    Password Security Checklist:
                  </Typography>
                  <List disablePadding>
                    <ListItem disablePadding sx={{ py: 0.25 }}>
                      <ListItemIcon sx={{ minWidth: 28 }}>
                        {criteria.length ? <CheckCircleRounded color="success" sx={{ fontSize: 18 }} /> : <RadioButtonUncheckedRounded sx={{ fontSize: 18 }} />}
                      </ListItemIcon>
                      <ListItemText 
                        primary={`At least ${policy.min_length} characters (Currently: ${newPassword.length})`}
                        primaryTypographyProps={{ fontSize: '0.8rem', color: criteria.length ? 'success.main' : 'text.secondary' }}
                      />
                    </ListItem>
                    
                    {policy.require_uppercase && (
                      <ListItem disablePadding sx={{ py: 0.25 }}>
                        <ListItemIcon sx={{ minWidth: 28 }}>
                          {criteria.uppercase ? <CheckCircleRounded color="success" sx={{ fontSize: 18 }} /> : <RadioButtonUncheckedRounded sx={{ fontSize: 18 }} />}
                        </ListItemIcon>
                        <ListItemText 
                          primary="At least one uppercase letter (A-Z)"
                          primaryTypographyProps={{ fontSize: '0.8rem', color: criteria.uppercase ? 'success.main' : 'text.secondary' }}
                        />
                      </ListItem>
                    )}

                    {policy.require_lowercase && (
                      <ListItem disablePadding sx={{ py: 0.25 }}>
                        <ListItemIcon sx={{ minWidth: 28 }}>
                          {criteria.lowercase ? <CheckCircleRounded color="success" sx={{ fontSize: 18 }} /> : <RadioButtonUncheckedRounded sx={{ fontSize: 18 }} />}
                        </ListItemIcon>
                        <ListItemText 
                          primary="At least one lowercase letter (a-z)"
                          primaryTypographyProps={{ fontSize: '0.8rem', color: criteria.lowercase ? 'success.main' : 'text.secondary' }}
                        />
                      </ListItem>
                    )}

                    {policy.require_numbers && (
                      <ListItem disablePadding sx={{ py: 0.25 }}>
                        <ListItemIcon sx={{ minWidth: 28 }}>
                          {criteria.number ? <CheckCircleRounded color="success" sx={{ fontSize: 18 }} /> : <RadioButtonUncheckedRounded sx={{ fontSize: 18 }} />}
                        </ListItemIcon>
                        <ListItemText 
                          primary="At least one number (0-9)"
                          primaryTypographyProps={{ fontSize: '0.8rem', color: criteria.number ? 'success.main' : 'text.secondary' }}
                        />
                      </ListItem>
                    )}

                    {policy.require_special && (
                      <ListItem disablePadding sx={{ py: 0.25 }}>
                        <ListItemIcon sx={{ minWidth: 28 }}>
                          {criteria.special ? <CheckCircleRounded color="success" sx={{ fontSize: 18 }} /> : <RadioButtonUncheckedRounded sx={{ fontSize: 18 }} />}
                        </ListItemIcon>
                        <ListItemText 
                          primary="At least one special character (e.g. !@#$%^&*)"
                          primaryTypographyProps={{ fontSize: '0.8rem', color: criteria.special ? 'success.main' : 'text.secondary' }}
                        />
                      </ListItem>
                    )}
                  </List>
                </Box>

                <LoadingButton variant="contained" loading={loading} onClick={handleResetPassword} disabled={!canSubmitPassword}>
                  Reset password
                </LoadingButton>
              </Stack>
            )}
          </Stack>
        </EnterpriseCard>
      </Box>
    </Box>
  )
}

