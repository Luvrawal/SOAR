import { AppRoutes } from './app/AppRoutes'
import { AuthProvider } from './app/AuthContext'

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App
