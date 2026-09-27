import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useMsal, useAccount } from '@azure/msal-react'
import { msalConfig, loginRequest } from '../authConfig'
import axios from 'axios'

export interface UserProfile {
  name: string
  email: string
  role: 'Standard User' | 'Platform Administrator' | 'Support Engineer' | 'Auditor'
}

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  user: UserProfile | null
  login: (mockUser?: { email: string; role: UserProfile['role'] }) => Promise<void>
  logout: () => Promise<void>
  getAccessToken: () => Promise<string | null>
  isMockMode: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const isMockAuthMode = msalConfig.auth.clientId === 'MOCK_CLIENT_ID'

function mapEntraRole(rawRoles: unknown): UserProfile['role'] {
  const roles = Array.isArray(rawRoles) ? rawRoles : []
  if (roles.some((role) => ['PlatformAdministrator', 'ITAdmin', 'IT Admin'].includes(String(role)))) {
    return 'Platform Administrator'
  }
  if (
    roles.some((role) =>
      ['SupportEngineer', 'Support Engineer', 'SoftwareRequestApprover', 'Approver', 'Manager'].includes(
        String(role),
      ),
    )
  ) {
    return 'Support Engineer'
  }
  if (roles.includes('Auditor')) return 'Auditor'
  return 'Standard User'
}

// MSAL Implementation for production Entra ID
function MsalAuthProvider({ children }: Readonly<{ children: ReactNode }>) {
  const { instance, accounts } = useMsal()
  const account = useAccount(accounts[0] || null)
  
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<UserProfile | null>(null)

  useEffect(() => {
    if (account) {
      setIsAuthenticated(true)
      const idTokenClaims = account.idTokenClaims as Record<string, unknown>
      const role = mapEntraRole(idTokenClaims?.roles)
      
      setUser({
        name: account.name ?? account.username,
        email: account.username,
        role,
      })
      setIsLoading(false)
    } else {
      instance
        .ssoSilent(loginRequest)
        .then((silentResult) => {
          if (silentResult && silentResult.account) {
            instance.setActiveAccount(silentResult.account)
            const idTokenClaims = silentResult.account.idTokenClaims as Record<string, unknown>
            const role = mapEntraRole(idTokenClaims?.roles)
            
            setUser({
              name: silentResult.account.name ?? silentResult.account.username,
              email: silentResult.account.username,
              role,
            })
            setIsAuthenticated(true)
          } else {
            setIsAuthenticated(false)
            setUser(null)
          }
        })
        .catch((error) => {
          console.warn('MSAL Silent SSO failed, user must sign in:', error)
          setIsAuthenticated(false)
          setUser(null)
        })
        .finally(() => {
          setIsLoading(false)
        })
    }
  }, [account, instance])

  const login = async () => {
    setIsLoading(true)
    try {
      await instance.loginRedirect(loginRequest)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      await instance.logoutRedirect()
    } finally {
      setIsLoading(false)
    }
  }

  const getAccessToken = async (): Promise<string | null> => {
    if (!account) return null
    try {
      const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account,
      })
      return response.accessToken
    } catch {
      try {
        const response = await instance.acquireTokenPopup(loginRequest)
        return response.accessToken
      } catch {
        return null
      }
    }
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        login,
        logout,
        getAccessToken,
        isMockMode: false,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// Standalone Mock Implementation without MSAL dependencies
function MockAuthProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<UserProfile | null>(null)

  useEffect(() => {
    const mockToken = localStorage.getItem('mockAccessToken')
    const savedUser = localStorage.getItem('mockUser')
    if (mockToken && savedUser) {
      try {
        setIsAuthenticated(true)
        setUser(JSON.parse(savedUser))
      } catch {
        localStorage.removeItem('mockAccessToken')
        localStorage.removeItem('mockUser')
      }
    }
    setIsLoading(false)
  }, [])

  const login = async (mockUser?: { email: string; role: UserProfile['role'] }) => {
    setIsLoading(true)
    try {
      if (!mockUser) {
        throw new Error('Mock user details are required in mock mode')
      }
      
      const apiBase = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
      const { data } = await axios.post(`${apiBase}/users/mock-token`, {
        email: mockUser.email,
        role: mockUser.role,
      })
      
      const loggedUser: UserProfile = {
        name: mockUser.email.split('@')[0],
        email: mockUser.email,
        role: mockUser.role,
      }
      
      localStorage.setItem('mockAccessToken', data.data.token)
      localStorage.setItem('mockUser', JSON.stringify(loggedUser))
      
      setUser(loggedUser)
      setIsAuthenticated(true)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      localStorage.removeItem('mockAccessToken')
      localStorage.removeItem('mockUser')
      setUser(null)
      setIsAuthenticated(false)
    } finally {
      setIsLoading(false)
    }
  }

  const getAccessToken = async (): Promise<string | null> => {
    return localStorage.getItem('mockAccessToken')
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        login,
        logout,
        getAccessToken,
        isMockMode: true,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function AuthProvider({ children }: Readonly<{ children: ReactNode }>) {
  if (isMockAuthMode) {
    return <MockAuthProvider>{children}</MockAuthProvider>
  }
  return <MsalAuthProvider>{children}</MsalAuthProvider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
