import { Box, Card, Stack, Typography, Grid, Divider } from '@mui/material'
import { VpnKeyRounded, AccessTimeRounded, InfoRounded, CodeRounded } from '@mui/icons-material'
import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { Header } from '../../components/Header'

export function SessionInfo() {
  const { getAccessToken, isMockMode, user } = useAuth()
  const [claims, setClaims] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    const fetchToken = async () => {
      const accessToken = await getAccessToken()
      
      if (accessToken) {
        try {
          const parts = accessToken.split('.')
          if (parts.length === 3) {
            const payload = JSON.parse(window.atob(parts[1]))
            setClaims(payload)
          } else {
            // Unstructured token (standard MSAL access tokens for MS Graph can be unstructured depending on tenant configuration)
            setClaims({
              note: "Microsoft Graph access tokens are sometimes encrypted or unstructured on the client side. This is standard behavior for Microsoft Entra ID. The user profile is mapped from local context.",
              user_email: user?.email,
              user_role: user?.role,
            })
          }
        } catch {
          setClaims({ error: "Failed to parse JWT payload." })
        }
      }
    }
    fetchToken()
  }, [getAccessToken, user])

  // Helpers to format dates
  const formatTime = (epoch?: number) => {
    if (!epoch) return 'N/A'
    return new Date(epoch * 1000).toLocaleString()
  }

  return (
    <Box>
      <Header
        title="Session Information"
        subtitle="Inspect your security tokens, expiration details, and corporate access scopes."
        breadcrumbs={[{ label: 'User Center' }, { label: 'Session Information' }]}
      />

      <Grid container spacing={3} sx={{ mt: 2, maxWidth: 900 }}>
        {/* Token details */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card
            sx={{
              p: 4,
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              height: '100%',
            }}
          >
            <Typography variant="h6" sx={{ fontWeight: 800, mb: 3 }}>
              Authentication Metadata
            </Typography>

            <Stack spacing={2.5}>
              <Stack direction="row" spacing={2} alignItems="center">
                <InfoRounded color="primary" />
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textTransform: 'uppercase', fontWeight: 700, fontSize: '0.65rem' }}>
                    Identity Provider
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {isMockMode ? 'Developer Local Mock Provider' : 'Microsoft Entra ID (Azure AD)'}
                  </Typography>
                </Box>
              </Stack>
              
              <Divider />

              <Stack direction="row" spacing={2} alignItems="center">
                <AccessTimeRounded color="primary" />
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textTransform: 'uppercase', fontWeight: 700, fontSize: '0.65rem' }}>
                    Issued At
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {claims?.iat ? formatTime(claims.iat as number) : 'Session Active'}
                  </Typography>
                </Box>
              </Stack>
              
              <Divider />

              <Stack direction="row" spacing={2} alignItems="center">
                <AccessTimeRounded color="error" />
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textTransform: 'uppercase', fontWeight: 700, fontSize: '0.65rem' }}>
                    Session Expiration
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {claims?.exp ? formatTime(claims.exp as number) : 'Closing Browser Ends Session'}
                  </Typography>
                </Box>
              </Stack>
              
              <Divider />

              <Stack direction="row" spacing={2} alignItems="center">
                <VpnKeyRounded color="primary" />
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textTransform: 'uppercase', fontWeight: 700, fontSize: '0.65rem' }}>
                    Access Scopes
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                    {(claims?.scp as string) ?? 'User.Read'}
                  </Typography>
                </Box>
              </Stack>
            </Stack>
          </Card>
        </Grid>

        {/* JWT Claims JSON Card */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Card
            sx={{
              p: 4,
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              bgcolor: '#0e1726', // dark code theme
              color: '#a5b4fc', // light indigo text
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
            }}
          >
            <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
              <CodeRounded sx={{ color: 'primary.light' }} />
              <Typography variant="h6" sx={{ fontWeight: 800, color: 'common.white' }}>
                Decoded JWT Claims
              </Typography>
            </Stack>

            <Box
              sx={{
                flexGrow: 1,
                overflow: 'auto',
                maxHeight: 400,
                p: 2,
                borderRadius: 2,
                bgcolor: 'rgba(0,0,0,0.3)',
                fontFamily: 'monospace',
                fontSize: '0.8rem',
                lineHeight: 1.5,
              }}
            >
              {claims ? (
                <pre style={{ margin: 0 }}>{JSON.stringify(claims, null, 2)}</pre>
              ) : (
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  No active token found to decode.
                </Typography>
              )}
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
