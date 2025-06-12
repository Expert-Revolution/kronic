import React, { useState } from 'react'
import { LoginFormData, ValidationErrors } from '../types/auth'
import { validateLoginForm } from '../utils/validation'
import { AuthService } from '../utils/authService'
import { useTranslation } from '../hooks/useTranslation'

interface LoginFormProps {
  onSuccess: () => void
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
    rememberMe: false
  })
  const [errors, setErrors] = useState<ValidationErrors>({})
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [generalError, setGeneralError] = useState('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
    
    // Clear error when user starts typing
    if (errors[name as keyof ValidationErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
    if (generalError) {
      setGeneralError('')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const validationErrors = validateLoginForm(formData)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    setIsLoading(true)
    setErrors({})
    setGeneralError('')

    try {
      await AuthService.login(formData)
      // Tokens are now handled via HTTP-only cookies
      AuthService.setRememberMe(formData.rememberMe)
      onSuccess()
    } catch (error: any) {
      setGeneralError(error.message || t('errors.loginFailed'))
    } finally {
      setIsLoading(false)
    }
  }

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  return (
    <div className="login-card">
      <div className="login-header">
        <h1 className="login-title">{t('login.title')}</h1>
        <p className="login-subtitle">{t('login.subtitle')}</p>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        {generalError && (
          <div className="error-message" role="alert">
            {generalError}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="email" className="form-label">
            {t('login.email')}
          </label>
          <input
            type="email"
            id="email"
            name="email"
            className="form-input"
            placeholder={t('login.emailPlaceholder')}
            value={formData.email}
            onChange={handleInputChange}
            aria-describedby={errors.email ? 'email-error' : undefined}
            aria-invalid={!!errors.email}
            autoComplete="email"
            required
          />
          {errors.email && (
            <div id="email-error" className="field-error" role="alert">
              {t(errors.email)}
            </div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="password" className="form-label">
            {t('login.password')}
          </label>
          <div className="password-input-container">
            <input
              type={showPassword ? 'text' : 'password'}
              id="password"
              name="password"
              className="form-input"
              placeholder={t('login.passwordPlaceholder')}
              value={formData.password}
              onChange={handleInputChange}
              aria-describedby={errors.password ? 'password-error' : undefined}
              aria-invalid={!!errors.password}
              autoComplete="current-password"
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={togglePasswordVisibility}
              aria-label={showPassword ? t('login.hidePassword') : t('login.showPassword')}
            >
              {showPassword ? '👁️' : '👁️‍🗨️'}
            </button>
          </div>
          {errors.password && (
            <div id="password-error" className="field-error" role="alert">
              {t(errors.password)}
            </div>
          )}
        </div>

        <div className="checkbox-container">
          <input
            type="checkbox"
            id="rememberMe"
            name="rememberMe"
            className="checkbox"
            checked={formData.rememberMe}
            onChange={handleInputChange}
          />
          <label htmlFor="rememberMe" className="checkbox-label">
            {t('login.rememberMe')}
          </label>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading}
          aria-describedby={isLoading ? 'loading-text' : undefined}
        >
          {isLoading ? (
            <>
              <span className="spinner" aria-hidden="true"></span>
              <span id="loading-text">{t('login.loggingIn')}</span>
            </>
          ) : (
            t('login.loginButton')
          )}
        </button>
      </form>

      <div className="login-footer">
        <p className="footer-text">
          <button
            type="button"
            className="btn-link"
            onClick={() => {/* TODO: Implement forgot password */}}
          >
            {t('login.forgotPassword')}
          </button>
        </p>
      </div>
    </div>
  )
}

export default LoginForm