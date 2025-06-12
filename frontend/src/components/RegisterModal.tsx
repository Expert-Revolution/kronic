import React, { useState } from 'react'
import { RegisterFormData, ValidationErrors } from '../types/auth'
import { validateRegisterForm } from '../utils/validation'
import { AuthService } from '../utils/authService'
import { useTranslation } from '../hooks/useTranslation'

interface RegisterModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

const RegisterModal: React.FC<RegisterModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { t } = useTranslation()
  const [formData, setFormData] = useState<RegisterFormData>({
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [errors, setErrors] = useState<ValidationErrors>({})
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [generalError, setGeneralError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
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
    
    const validationErrors = validateRegisterForm(formData)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    setIsLoading(true)
    setErrors({})
    setGeneralError('')

    try {
      await AuthService.register(formData)
      setSuccessMessage(t('success.accountCreated'))
      setFormData({ email: '', password: '', confirmPassword: '' })
      
      // Close modal after 2 seconds
      setTimeout(() => {
        setSuccessMessage('')
        onSuccess()
        onClose()
      }, 2000)
    } catch (error: any) {
      setGeneralError(error.message || t('errors.registrationFailed'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    setFormData({ email: '', password: '', confirmPassword: '' })
    setErrors({})
    setGeneralError('')
    setSuccessMessage('')
    onClose()
  }

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  const toggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword)
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{t('register.title')}</h2>
          <button
            type="button"
            className="modal-close"
            onClick={handleClose}
            aria-label={t('register.close')}
          >
            ×
          </button>
        </div>

        <div className="modal-body">
          <form onSubmit={handleSubmit} noValidate>
            {generalError && (
              <div className="error-message" role="alert">
                {generalError}
              </div>
            )}

            {successMessage && (
              <div className="success-message" role="alert">
                {successMessage}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="reg-email" className="form-label">
                {t('register.email')}
              </label>
              <input
                type="email"
                id="reg-email"
                name="email"
                className="form-input"
                placeholder={t('register.emailPlaceholder')}
                value={formData.email}
                onChange={handleInputChange}
                aria-describedby={errors.email ? 'reg-email-error' : undefined}
                aria-invalid={!!errors.email}
                autoComplete="email"
                required
              />
              {errors.email && (
                <div id="reg-email-error" className="field-error" role="alert">
                  {t(errors.email)}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="reg-password" className="form-label">
                {t('register.password')}
              </label>
              <div className="password-input-container">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="reg-password"
                  name="password"
                  className="form-input"
                  placeholder={t('register.passwordPlaceholder')}
                  value={formData.password}
                  onChange={handleInputChange}
                  aria-describedby={errors.password ? 'reg-password-error password-hint' : 'password-hint'}
                  aria-invalid={!!errors.password}
                  autoComplete="new-password"
                  minLength={8}
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
              <div id="password-hint" className="field-error" style={{ color: 'var(--text-secondary)' }}>
                {t('register.passwordHint')}
              </div>
              {errors.password && (
                <div id="reg-password-error" className="field-error" role="alert">
                  {t(errors.password)}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="reg-confirm-password" className="form-label">
                {t('register.confirmPassword')}
              </label>
              <div className="password-input-container">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="reg-confirm-password"
                  name="confirmPassword"
                  className="form-input"
                  placeholder={t('register.confirmPasswordPlaceholder')}
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  aria-describedby={errors.confirmPassword ? 'reg-confirm-password-error' : undefined}
                  aria-invalid={!!errors.confirmPassword}
                  autoComplete="new-password"
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={toggleConfirmPasswordVisibility}
                  aria-label={showConfirmPassword ? t('login.hidePassword') : t('login.showPassword')}
                >
                  {showConfirmPassword ? '👁️' : '👁️‍🗨️'}
                </button>
              </div>
              {errors.confirmPassword && (
                <div id="reg-confirm-password-error" className="field-error" role="alert">
                  {t(errors.confirmPassword)}
                </div>
              )}
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={isLoading}
              aria-describedby={isLoading ? 'reg-loading-text' : undefined}
            >
              {isLoading ? (
                <>
                  <span className="spinner" aria-hidden="true"></span>
                  <span id="reg-loading-text">{t('register.creating')}</span>
                </>
              ) : (
                t('register.registerButton')
              )}
            </button>
          </form>

          <div className="login-footer">
            <p className="footer-text">
              {t('register.hasAccount')}{' '}
              <button
                type="button"
                className="btn-link"
                onClick={handleClose}
              >
                {t('register.signIn')}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RegisterModal