import axios from 'axios'

const passwordApiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
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
  return postPasswordRequest('/password/forgot-password', { email }, 'Unable to send an OTP. Please try again.')
}

export async function verifyOtp(email: string, otp: string): Promise<PasswordApiResult> {
  return postPasswordRequest('/password/verify-otp', { email, otp }, 'Unable to verify the OTP. Please try again.')
}
