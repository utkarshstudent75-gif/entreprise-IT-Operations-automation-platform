import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

import { PublicClientApplication } from '@azure/msal-browser'
import { MsalProvider } from '@azure/msal-react'
import { msalConfig } from './authConfig'
import { AuthProvider, isMockAuthMode } from './contexts/AuthContext'

const theme = createTheme({
  palette: {
    primary: { main: '#155fc1', dark: '#0b3a82' },
    background: { default: '#f5f8ff' },
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    button: { fontWeight: 700, textTransform: 'none' },
  },
  components: {
    MuiButton: { styleOverrides: { root: { borderRadius: 10, minHeight: 46 } } },
    MuiOutlinedInput: { styleOverrides: { root: { backgroundColor: '#fff' } } },
  },
})

const root = createRoot(document.getElementById('root')!)

const renderApp = (wrapMsal = false, msalInstance?: PublicClientApplication) => {
  const content = (
    <AuthProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </AuthProvider>
  )

  if (wrapMsal && msalInstance) {
    root.render(
      <StrictMode>
        <MsalProvider instance={msalInstance}>{content}</MsalProvider>
      </StrictMode>,
    )
  } else {
    root.render(<StrictMode>{content}</StrictMode>)
  }
}

if (isMockAuthMode) {
  // Mock mode: Synchronous immediate render without external MSAL network overhead
  renderApp(false)
} else {
  // Entra ID mode: Initialize MSAL client before rendering MsalProvider
  const msalInstance = new PublicClientApplication(msalConfig)
  msalInstance
    .initialize()
    .then(() => {
      renderApp(true, msalInstance)
    })
    .catch((error) => {
      console.error('Failed to initialize MSAL, rendering with fallback:', error)
      renderApp(false)
    })
}
