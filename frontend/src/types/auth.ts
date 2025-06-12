export interface LoginFormData {
  email: string
  password: string
  rememberMe: boolean
}

export interface RegisterFormData {
  email: string
  password: string
  confirmPassword: string
}

export interface AuthResponse {
  token: string
  refresh_token: string
  user?: {
    email: string
  }
}

export interface AuthError {
  error: string
}

export class AuthError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'AuthError'
  }
}

export interface ValidationErrors {
  email?: string
  password?: string
  confirmPassword?: string
  general?: string
}

export type Theme = 'light' | 'dark'
export type Language = 'en' | 'es'