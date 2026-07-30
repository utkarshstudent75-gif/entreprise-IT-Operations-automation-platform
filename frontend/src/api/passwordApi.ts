import axios from 'axios'

const passwordApiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export interface PasswordApiResponse {
  message: string
}

export interface PasswordApiResult {
  message: string
  success: boolean
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<{ detail?: string; message?: string }>(error)) {
    return error.response?.data?.detail ?? error.response?.data?.message ?? fallback
  }

  return fallback
}

async function postPasswordRequest(
  path: string,
  payload: Record<string, string>,
  fallbackMessage: string,
): Promise<PasswordApiResult> {
  try {
    const { data } = await passwordApiClient.post<PasswordApiResponse>(path, payload)
    return { message: data.message, success: true }
  } catch (error) {
    return { message: getErrorMessage(error, fallbackMessage), success: false }
  }
}

export async function requestPasswordReset(email: string): Promise<PasswordApiResult> {
  return postPasswordRequest('/password/forgot-password', { email }, 'Unable to send a reset code. Please try again.')
}

export async function verifyOtp(email: string, otp: string): Promise<PasswordApiResult> {
  return postPasswordRequest('/password/verify-otp', { email, otp }, 'Unable to verify the reset code. Please try again.')
}

export async function resetPassword(email: string, otp: string, new_password: string, confirm_password?: string): Promise<PasswordApiResult> {
  const payload: Record<string, string> = { email, otp, new_password }
  if (confirm_password) {
    payload.confirm_password = confirm_password
  }
  return postPasswordRequest('/password/reset-password', payload, 'Unable to reset your password. Please try again.')
}

export interface PasswordPolicy {
  min_length: number
  require_uppercase: boolean
  require_lowercase: boolean
  require_numbers: boolean
  require_special: boolean
}

export async function getPasswordPolicy(): Promise<PasswordPolicy> {
  try {
    const { data } = await passwordApiClient.get<{ success: boolean, data: PasswordPolicy }>('/password/policy')
    return data.data
  } catch {
    // Fallback to standard enterprise settings on failure
    return {
      min_length: 12,
      require_uppercase: true,
      require_lowercase: true,
      require_numbers: true,
      require_special: true,
    }
  }
}

