import axios from 'axios'

const userApiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

export interface CreateUserPayload {
  username: string
  email: string
  password: string
}

export interface CreateUserResponse {
  id: number
  username: string
  email: string
}

export interface UserApiResult {
  message: string
  success: boolean
  data?: CreateUserResponse
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<{ detail?: string; message?: string }>(error)) {
    return error.response?.data?.detail ?? error.response?.data?.message ?? fallback
  }

  return fallback
}

export async function createUser(payload: CreateUserPayload): Promise<UserApiResult> {
  try {
    const { data } = await userApiClient.post<CreateUserResponse>('/users', payload)

    return {
      success: true,
      message: 'User created successfully.',
      data,
    }
  } catch (error) {
    return {
      success: false,
      message: getErrorMessage(error, 'Unable to create user. Please try again.'),
    }
  }
}
