import axios from 'axios'

const passwordApiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

export interface PasswordApiResponse {
  message: string
}

export async function requestPasswordReset(email: string): Promise<PasswordApiResponse> {
  const { data } = await passwordApiClient.post<PasswordApiResponse>('/password/forgot-password', { email })
  return data
}

export async function verifyOtp(email: string, otp: string): Promise<PasswordApiResponse> {
  const { data } = await passwordApiClient.post<PasswordApiResponse>('/password/verify-otp', { email, otp })
  return data
}
