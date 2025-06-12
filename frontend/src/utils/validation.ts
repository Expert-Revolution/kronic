import { LoginFormData, RegisterFormData, ValidationErrors } from '../types/auth'

export const validateEmail = (email: string): string | undefined => {
  if (!email.trim()) {
    return 'validation.required'
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    return 'validation.invalidEmail'
  }
  return undefined
}

export const validatePassword = (password: string): string | undefined => {
  if (!password) {
    return 'validation.required'
  }
  if (password.length < 8) {
    return 'validation.passwordTooShort'
  }
  // Check for uppercase, lowercase, number, and special character
  const hasUpperCase = /[A-Z]/.test(password)
  const hasLowerCase = /[a-z]/.test(password)
  const hasNumbers = /\d/.test(password)
  const hasNonalphas = /\W/.test(password)
  
  if (!(hasUpperCase && hasLowerCase && hasNumbers && hasNonalphas)) {
    return 'validation.passwordWeak'
  }
  return undefined
}

export const validateConfirmPassword = (password: string, confirmPassword: string): string | undefined => {
  if (!confirmPassword) {
    return 'validation.required'
  }
  if (password !== confirmPassword) {
    return 'validation.passwordsDoNotMatch'
  }
  return undefined
}

export const validateLoginForm = (formData: LoginFormData): ValidationErrors => {
  const errors: ValidationErrors = {}
  
  const emailError = validateEmail(formData.email)
  if (emailError) {
    errors.email = emailError
  }
  
  if (!formData.password) {
    errors.password = 'validation.required'
  }
  
  return errors
}

export const validateRegisterForm = (formData: RegisterFormData): ValidationErrors => {
  const errors: ValidationErrors = {}
  
  const emailError = validateEmail(formData.email)
  if (emailError) {
    errors.email = emailError
  }
  
  const passwordError = validatePassword(formData.password)
  if (passwordError) {
    errors.password = passwordError
  }
  
  const confirmPasswordError = validateConfirmPassword(formData.password, formData.confirmPassword)
  if (confirmPasswordError) {
    errors.confirmPassword = confirmPasswordError
  }
  
  return errors
}