/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useEffect } from 'react'
import { PublicClientApplication, Configuration, InteractionRequiredAuthError } from '@azure/msal-browser'
import { useMsal, useAccount } from '@azure/msal-react'

// Conditional or fallback config for MSAL
const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID || 'placeholder-client-id',
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID || 'common'}`,
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage',
  },
}

export const msalInstance = new PublicClientApplication(msalConfig)

interface AuthContextType {
  isAuthenticated: boolean
  userEmail: string | null
  userName: string | null
  userRole: string | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithMicrosoft: () => Promise<void>
  logout: () => Promise<void>
  authProvider: 'local' | 'entra'
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const authProvider = (import.meta.env.VITE_AUTH_PROVIDER || 'local') as 'local' | 'entra'
  
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [userName, setUserName] = useState<string | null>(null)
  const [userRole, setUserRole] = useState<string | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  // Call MSAL hooks unconditionally (safe because MsalProvider is always present)
  const { instance, accounts } = useMsal()
  const account = useAccount(accounts ? accounts[0] : undefined)

  // Initialize and synchronize state
  useEffect(() => {
    if (authProvider === 'local') {
      const isAuth = localStorage.getItem('isAuthenticated') === 'true'
      const storedEmail = localStorage.getItem('userEmail')
      const storedToken = localStorage.getItem('authToken')
      const storedName = localStorage.getItem('userName') || storedEmail
      const storedRole = localStorage.getItem('userRole') || 'HelpDesk'

      if (isAuth && storedToken) {
        setIsAuthenticated(true)
        setUserEmail(storedEmail)
        setToken(storedToken)
        setUserName(storedName)
        setUserRole(storedRole)
      } else {
        setIsAuthenticated(false)
        setUserEmail(null)
        setToken(null)
        setUserName(null)
        setUserRole(null)
      }
      setLoading(false)
    } else {
      // Entra ID flow
      if (accounts && accounts.length > 0 && account) {
        // Request token silently
        instance.acquireTokenSilent({
          scopes: ['openid', 'profile', 'email', 'User.Read'],
          account: account,
        }).then((response) => {
          setIsAuthenticated(true)
          setUserEmail(account.username)
          setUserName(account.name || account.username)
          setToken(response.idToken)
          // Store role if available, or default to HelpDesk for now
          const role = 'HelpDesk'
          setUserRole(role)

          localStorage.setItem('isAuthenticated', 'true')
          localStorage.setItem('userEmail', account.username)
          localStorage.setItem('authToken', response.idToken)
          localStorage.setItem('userName', account.name || account.username)
          localStorage.setItem('userRole', role)
          
          setLoading(false)
        }).catch((err) => {
          console.warn('Acquire token silent failed, trying interactive:', err)
          if (err instanceof InteractionRequiredAuthError) {
            instance.acquireTokenRedirect({
              scopes: ['openid', 'profile', 'email', 'User.Read'],
              account: account,
            })
          }
          setLoading(false)
        })
      } else {
        const isAuth = localStorage.getItem('isAuthenticated') === 'true'
        if (!isAuth) {
          setIsAuthenticated(false)
          setUserEmail(null)
          setToken(null)
          setUserName(null)
          setUserRole(null)
          localStorage.removeItem('isAuthenticated')
          localStorage.removeItem('userEmail')
          localStorage.removeItem('authToken')
          localStorage.removeItem('userName')
          localStorage.removeItem('userRole')
        } else {
          // Sync with local state until MSAL accounts list completes loading
          const storedEmail = localStorage.getItem('userEmail')
          const storedToken = localStorage.getItem('authToken')
          const storedName = localStorage.getItem('userName')
          const storedRole = localStorage.getItem('userRole')
          
          if (storedToken) {
            setIsAuthenticated(true)
            setUserEmail(storedEmail)
            setToken(storedToken)
            setUserName(storedName)
            setUserRole(storedRole)
          } else {
            setIsAuthenticated(false)
          }
        }
        setLoading(false)
      }
    }
  }, [accounts, account, instance, authProvider])

  const login = async (email: string, password: string) => {
    if (authProvider !== 'local') return
    setLoading(true)
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/users/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username_or_email: email, password }),
      })
      const resData = await response.json()
      if (!response.ok || !resData.success) {
        throw new Error(resData.error?.message || 'Login failed')
      }
      const data = resData.data
      setIsAuthenticated(true)
      setUserEmail(data.user.email)
      setToken(data.access_token)
      setUserName(data.user.username)
      setUserRole(data.user.roles || 'HelpDesk')

      localStorage.setItem('isAuthenticated', 'true')
      localStorage.setItem('userEmail', data.user.email)
      localStorage.setItem('authToken', data.access_token)
      localStorage.setItem('userName', data.user.username)
      localStorage.setItem('userRole', data.user.roles || 'HelpDesk')
    } finally {
      setLoading(false)
    }
  }

  const loginWithMicrosoft = async () => {
    if (authProvider !== 'entra') return
    setLoading(true)
    try {
      await instance.loginRedirect({
        scopes: ['openid', 'profile', 'email', 'User.Read'],
      })
    } catch (err) {
      console.error('Microsoft login failed:', err)
      setLoading(false)
    }
  }

  const logout = async () => {
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('authToken')
    localStorage.removeItem('userName')
    localStorage.removeItem('userRole')
    
    setIsAuthenticated(false)
    setUserEmail(null)
    setToken(null)
    setUserName(null)
    setUserRole(null)

    if (authProvider === 'entra') {
      try {
        await instance.logoutRedirect()
      } catch (err) {
        console.error('MSAL logout redirect failed:', err)
      }
    }
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        userEmail,
        userName,
        userRole,
        token,
        loading,
        login,
        loginWithMicrosoft,
        logout,
        authProvider,
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
