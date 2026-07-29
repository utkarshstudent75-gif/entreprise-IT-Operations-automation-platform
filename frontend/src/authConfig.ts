import { Configuration, PopupRequest } from '@azure/msal-browser'

// Use VITE_ prefix for environment variables compiled by Vite
export const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID ?? 'MOCK_CLIENT_ID',
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID ?? 'common'}`,
    redirectUri: import.meta.env.VITE_ENTRA_REDIRECT_URI ?? window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'sessionStorage', // standard for web apps to avoid cookie overhead
    storeAuthStateInCookie: false,
  },
}

// Scopes required for dashboard login profile read
export const loginRequest: PopupRequest = {
  scopes: ['User.Read'],
}
