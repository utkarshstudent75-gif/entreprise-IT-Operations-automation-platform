import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom'
import { PublicLayout } from './layouts/PublicLayout'
import { DashboardLayout } from './layouts/DashboardLayout'
import { ProtectedRoute } from './components/ProtectedRoute'

// Public Pages
import { LandingPage } from './pages/public/LandingPage'
import { Login } from './pages/public/Login'
import { PasswordReset } from './pages/public/PasswordReset'
import { VerifyOTP } from './pages/public/VerifyOTP'
import { ResetPassword } from './pages/public/ResetPassword'
import { PasswordResetPage } from './pages/PasswordResetPage'


// Protected Pages
import { Dashboard } from './pages/protected/Dashboard'
import { ProtectedPasswordReset } from './pages/protected/PasswordReset'
import { MFAReset } from './pages/protected/MFAReset'
import { UnlockAccount } from './pages/protected/UnlockAccount'
import { SoftwareRequest } from './pages/protected/SoftwareRequest'
import { AccessRequest } from './pages/protected/AccessRequest'
import { LicenseAssignment } from './pages/protected/LicenseAssignment'
import { MyRequests } from './pages/protected/MyRequests'
import { MyTickets } from './pages/protected/MyTickets'
import { AIAssistant } from './pages/protected/AIAssistant'
import { AdminDashboard } from './pages/protected/AdminDashboard'

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
        <Route
          path="/dashboard/password-reset"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <ProtectedPasswordReset />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/mfa-reset"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MFAReset />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/unlock-account"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <UnlockAccount />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/software-request"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <SoftwareRequest />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/access-request"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AccessRequest />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/license-assignment"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <LicenseAssignment />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/my-requests"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MyRequests />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/my-tickets"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MyTickets />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/ai-assistant"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <AIAssistant />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/admin"
          element={
            <ProtectedRoute>
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
            <ProtectedRoute>
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
