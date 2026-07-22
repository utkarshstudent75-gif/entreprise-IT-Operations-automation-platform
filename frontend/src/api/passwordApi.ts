import axios from 'axios'
import { apiClient } from './apiClient'

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
    const { data } = await apiClient.post<PasswordApiResponse>(path, payload)
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

export async function resetPassword(email: string, otp: string, new_password: string): Promise<PasswordApiResult> {
  return postPasswordRequest('/password/reset-password', { email, otp, new_password }, 'Unable to reset your password. Please try again.')
}
