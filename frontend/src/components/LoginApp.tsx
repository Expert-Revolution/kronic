import React, { useState } from 'react'
import { useTheme } from '../hooks/useTheme'
import { useTranslation } from '../hooks/useTranslation'
import LoginForm from './LoginForm'
import RegisterModal from './RegisterModal'
import { Language } from '../types/auth'

const LoginApp: React.FC = () => {
  const { theme, toggleTheme } = useTheme()
  const { language, setLanguage } = useTranslation()
  const [showRegister, setShowRegister] = useState(false)

  const handleLoginSuccess = () => {
    // Redirect to dashboard
    window.location.href = '/'
  }

  const handleRegisterSuccess = () => {
    setShowRegister(false)
  }

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLanguage(e.target.value as Language)
  }

  return (
    <>
      <div className="login-container">
        <div className="controls-container">
          <button
            className="control-btn"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          
          <select
            className="language-select"
            value={language}
            onChange={handleLanguageChange}
            aria-label="Select language"
          >
            <option value="en">🇺🇸 EN</option>
            <option value="es">🇪🇸 ES</option>
          </select>
        </div>

        <LoginForm
          onSuccess={handleLoginSuccess}
          onShowRegister={() => setShowRegister(true)}
        />
      </div>

      <RegisterModal
        isOpen={showRegister}
        onClose={() => setShowRegister(false)}
        onSuccess={handleRegisterSuccess}
      />
    </>
  )
}

export default LoginApp