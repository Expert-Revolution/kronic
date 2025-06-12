import React from 'react'
import { useTheme } from '../hooks/useTheme'
import { useTranslation } from '../hooks/useTranslation'
import LoginForm from './LoginForm'
import { Language } from '../types/auth'

const LoginApp: React.FC = () => {
  const { theme, toggleTheme } = useTheme()
  const { language, setLanguage } = useTranslation()

  const handleLoginSuccess = () => {
    // Redirect to dashboard
    window.location.href = '/'
  }

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLanguage(e.target.value as Language)
  }

  return (
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

      <LoginForm onSuccess={handleLoginSuccess} />
    </div>
  )
}

export default LoginApp