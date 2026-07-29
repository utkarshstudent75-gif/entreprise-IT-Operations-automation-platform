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

export function AuthProvider({ children }: Readonly<{ children: ReactNode }>) {
  const { instance, accounts } = useMsal()
  const account = useAccount(accounts[0] || null)
  
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<UserProfile | null>(null)
  
  // Detect if MSAL is running in mock mode (i.e. no Client ID set)
  const isMockMode = msalConfig.auth.clientId === 'MOCK_CLIENT_ID'

  // Initialize session
  useEffect(() => {
    const initializeAuth = async () => {
      if (isMockMode) {
        // Read local mock session
        const mockToken = localStorage.getItem('mockAccessToken')
        const savedUser = localStorage.getItem('mockUser')
        if (mockToken && savedUser) {
          setIsAuthenticated(true)
          setUser(JSON.parse(savedUser))
        }
        setIsLoading(false)
      } else {
        // Use MSAL
        if (account) {
          setIsAuthenticated(true)
          // Extract roles from MSAL claims if present
          const idTokenClaims = account.idTokenClaims as Record<string, any>
          const rawRoles: string[] = idTokenClaims?.roles ?? []
          
          let role: UserProfile['role'] = 'Standard User'
          if (rawRoles.includes('PlatformAdministrator')) {
            role = 'Platform Administrator'
          } else if (rawRoles.includes('SupportEngineer')) {
            role = 'Support Engineer'
          } else if (rawRoles.includes('Auditor')) {
            role = 'Auditor'
          }
          
          setUser({
            name: account.name ?? account.username,
            email: account.username,
            role,
          })
        } else {
          setIsAuthenticated(false)
          setUser(null)
        }
        setIsLoading(false)
      }
    }
    initializeAuth()
  }, [account, isMockMode])

  const login = async (mockUser?: { email: string; role: UserProfile['role'] }) => {
    setIsLoading(true)
    try {
      if (isMockMode) {
        if (!mockUser) {
          throw new Error('Mock user details are required in mock mode')
        }
        
        // Fetch a signed mock token from the backend
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
      } else {
        // Trigger MSAL popup login
        await instance.loginPopup(loginRequest)
      }
    } catch (error) {
      console.error('Login failed:', error)
      throw error;
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      if (isMockMode) {
        localStorage.removeItem('mockAccessToken')
        localStorage.removeItem('mockUser')
        setUser(null)
        setIsAuthenticated(false)
      } else {
        await instance.logoutPopup()
      }
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getAccessToken = async (): Promise<string | null> => {
    if (isMockMode) {
      return localStorage.getItem('mockAccessToken')
    }
    
    if (!account) return null
    
    try {
      // MSAL silent token refresh
      const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account,
      })
      return response.accessToken
    } catch (error) {
      console.warn('Silent token acquisition failed, acquiring via popup:', error)
      try {
        const response = await instance.acquireTokenPopup(loginRequest)
        return response.accessToken
      } catch (popupError) {
        console.error('Popup token acquisition failed:', popupError)
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
        isMockMode,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
