import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

interface StandardResponse<T> {
  success: boolean
  data: T
}

interface ApiErrorPayload {
  detail?: unknown
  error?: { message?: string }
}

export interface AccountUnlockRequest {
  id: number
  requester_email: string
  justification: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  created_at: string
}

export interface SoftwareRequest {
  id: number
  software_name: string
  justification: string
  requester_email: string | null
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  decided_by_email: string | null
  decision_note: string | null
  created_at: string
  updated_at: string
  decided_at: string | null
}

export function getOperationsApiError(error: unknown, fallback: string): string {
  if (axios.isAxiosError<ApiErrorPayload>(error)) {
    const payload = error.response?.data
    if (payload?.error?.message) return payload.error.message
    if (typeof payload?.detail === 'string') return payload.detail
  }
  return fallback
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` }
}

export async function createAccountUnlockRequest(
  token: string,
  email: string,
  justification: string,
): Promise<AccountUnlockRequest> {
  const { data } = await apiClient.post<StandardResponse<AccountUnlockRequest>>(
    '/identity/unlock-requests',
    { email, justification },
    { headers: authHeaders(token) },
  )
  return data.data
}

export async function getPendingAccountUnlockRequests(
  token: string,
): Promise<AccountUnlockRequest[]> {
  const { data } = await apiClient.get<StandardResponse<AccountUnlockRequest[]>>(
    '/identity/unlock-requests/pending',
    { headers: authHeaders(token) },
  )
  return data.data
}

export async function resetMfa(token: string, email: string): Promise<string> {
  const { data } = await apiClient.post<
    StandardResponse<{ message: string; methods_removed: number }>
  >('/mfa/reset', { email }, { headers: authHeaders(token) })
  return data.data.message
}

export async function createSoftwareRequest(
  token: string,
  softwareName: string,
  justification: string,
): Promise<SoftwareRequest> {
  const { data } = await apiClient.post<StandardResponse<SoftwareRequest>>(
    '/software',
    { software_name: softwareName, justification },
    { headers: authHeaders(token) },
  )
  return data.data
}

export async function getMySoftwareRequests(
  token: string,
): Promise<SoftwareRequest[]> {
  const { data } = await apiClient.get<StandardResponse<SoftwareRequest[]>>(
    '/software/mine',
    { headers: authHeaders(token) },
  )
  return data.data
}

export async function getPendingSoftwareRequests(
  token: string,
): Promise<SoftwareRequest[]> {
  const { data } = await apiClient.get<StandardResponse<SoftwareRequest[]>>(
    '/software/pending',
    { headers: authHeaders(token) },
  )
  return data.data
}

export async function decideSoftwareRequest(
  token: string,
  requestId: number,
  decision: 'approve' | 'reject',
): Promise<SoftwareRequest> {
  const { data } = await apiClient.post<StandardResponse<SoftwareRequest>>(
    `/software/${requestId}/${decision}`,
    {},
    { headers: authHeaders(token) },
  )
  return data.data
}
