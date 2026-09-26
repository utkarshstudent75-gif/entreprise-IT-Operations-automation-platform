import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

import { PublicClientApplication } from '@azure/msal-browser'
import { MsalProvider } from '@azure/msal-react'
import { msalConfig } from './authConfig'
import { AuthProvider } from './contexts/AuthContext'

const msalInstance = new PublicClientApplication(msalConfig)

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

// MSAL Browser v3 requires initialize() before any MSAL calls or MsalProvider mount
msalInstance
  .initialize()
  .then(() => {
    root.render(
      <StrictMode>
        <MsalProvider instance={msalInstance}>
          <AuthProvider>
            <ThemeProvider theme={theme}>
              <CssBaseline />
              <App />
            </ThemeProvider>
          </AuthProvider>
        </MsalProvider>
      </StrictMode>,
    )
  })
  .catch((error) => {
    console.error('Failed to initialize MSAL:', error)
    root.render(
      <StrictMode>
        <MsalProvider instance={msalInstance}>
          <AuthProvider>
            <ThemeProvider theme={theme}>
              <CssBaseline />
              <App />
            </ThemeProvider>
          </AuthProvider>
        </MsalProvider>
      </StrictMode>,
    )
  })

