import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ContentShell } from './components/ContentShell'
import { AdminCreateUserPage } from './pages/AdminCreateUserPage'
import { PasswordResetPage } from './pages/PasswordResetPage'

function App() {
  return (
    <BrowserRouter>
      <ContentShell>
        <Routes>
          <Route path="/" element={<PasswordResetPage />} />
          <Route path="/admin/create-user" element={<AdminCreateUserPage />} />
        </Routes>
      </ContentShell>
    </BrowserRouter>
  )
}

export default App
