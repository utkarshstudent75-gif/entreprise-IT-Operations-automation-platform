import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import { PublicLayout } from './layouts/PublicLayout'
import { DashboardLayout } from './layouts/DashboardLayout'
import { ProtectedRoute } from './components/ProtectedRoute'

// Public Pages
import { LandingPage } from './pages/public/LandingPage'
import { Login } from './pages/public/Login'
import { VerifyOTP } from './pages/public/VerifyOTP'
import { ResetPassword } from './pages/public/ResetPassword'
import { PasswordResetPage } from './pages/PasswordResetPage'

// Protected Pages
import { Dashboard } from './pages/protected/Dashboard'
import { ProtectedPasswordReset } from './pages/protected/PasswordReset'
import { MFAReset } from './pages/protected/MFAReset'
import { UnlockAccount } from './pages/protected/UnlockAccount'
import { SoftwareRequest } from './pages/protected/SoftwareRequest'
import { SoftwareApprovals } from './pages/protected/SoftwareApprovals'
import { AccessRequest } from './pages/protected/AccessRequest'
import { LicenseAssignment } from './pages/protected/LicenseAssignment'
import { MyRequests } from './pages/protected/MyRequests'
import { MyTickets } from './pages/protected/MyTickets'
import { AIAssistant } from './pages/protected/AIAssistant'
import { AdminDashboard } from './pages/protected/AdminDashboard'

// New User Center Protected Pages
import { MyProfile } from './pages/protected/MyProfile'
import { PasswordResetHistory } from './pages/protected/PasswordResetHistory'
import { SessionInfo } from './pages/protected/SessionInfo'
import { NotificationCenter } from './pages/protected/NotificationCenter'
import { VpnRequest } from './pages/protected/VpnRequest'
import { MailboxRequest } from './pages/protected/MailboxRequest'
import { MfaManagement } from './pages/protected/MfaManagement'
import { SettingsPage } from './pages/protected/SettingsPage'
import { HelpPage } from './pages/protected/HelpPage'

// Keep old route imports/aliases
import { AdminCreateUserPage } from './pages/AdminCreateUserPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes with PublicLayout */}
        <Route
          path="/"
          element={
            <PublicLayout>
              <LandingPage />
            </PublicLayout>
          }
        />
        <Route
          path="/login"
          element={
            <PublicLayout>
              <Login />
            </PublicLayout>
          }
        />
        <Route
          path="/password-reset"
          element={
            <PublicLayout>
              <PasswordResetPage />
            </PublicLayout>
          }
        />

        <Route
          path="/verify-otp"
          element={
            <PublicLayout>
              <VerifyOTP />
            </PublicLayout>
          }
        />
        <Route
          path="/reset-password"
          element={
            <PublicLayout>
              <ResetPassword />
            </PublicLayout>
          }
        />

        {/* Protected Routes with DashboardLayout */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <Dashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        
        {/* User Center Protected Routes */}
        <Route
          path="/dashboard/profile"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MyProfile />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/reset-history"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <PasswordResetHistory />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/session-info"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <SessionInfo />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/notifications"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <NotificationCenter />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/dashboard/password-reset"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <ProtectedPasswordReset />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/mfa-reset"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <MFAReset />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/unlock-account"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <UnlockAccount />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/software-request"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <SoftwareRequest />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/software-approvals"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer']}>
              <DashboardLayout>
                <SoftwareApprovals />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/vpn-request"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <VpnRequest />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/mailbox-request"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <MailboxRequest />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/mfa-management"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <MfaManagement />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/settings"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <SettingsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/help"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <HelpPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/access-request"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer']}>
              <DashboardLayout>
                <AccessRequest />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/license-assignment"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator']}>
              <DashboardLayout>
                <LicenseAssignment />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/my-requests"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <MyRequests />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/my-tickets"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer']}>
              <DashboardLayout>
                <MyTickets />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/ai-assistant"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator', 'Support Engineer', 'Standard User']}>
              <DashboardLayout>
                <AIAssistant />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/admin"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator']}>
              <DashboardLayout>
                <AdminDashboard />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* Backwards Compatibility / Alias for Admin Create User */}
        <Route
          path="/admin/create-user"
          element={
            <ProtectedRoute allowedRoles={['Platform Administrator']}>
              <DashboardLayout>
                <AdminCreateUserPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />

        {/* Fallback redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
