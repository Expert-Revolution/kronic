import { LoginFormData, RegisterFormData, AuthResponse } from '../types/auth'
import { AuthError } from '../types/auth'

const API_BASE = '/api/auth'

export class AuthService {
  static async login(formData: LoginFormData): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: formData.email,
        password: formData.password
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new AuthError(data.error || 'Login failed')
    }

    return data
  }

  static async register(formData: RegisterFormData): Promise<void> {
    const response = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: formData.email,
        password: formData.password
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new AuthError(data.error || 'Registration failed')
    }
  }

  static async checkAuth(): Promise<{ authenticated: boolean; user?: any }> {
    const token = this.getToken()
    if (!token) {
      return { authenticated: false }
    }

    const response = await fetch(`${API_BASE}/check-auth`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      this.clearTokens()
      return { authenticated: false }
    }

    const data = await response.json()
    return data
  }

  static storeTokens(token: string, refreshToken: string): void {
    localStorage.setItem('authToken', token)
    localStorage.setItem('refreshToken', refreshToken)
  }

  static getToken(): string | null {
    return localStorage.getItem('authToken')
  }

  static getRefreshToken(): string | null {
    return localStorage.getItem('refreshToken')
  }

  static clearTokens(): void {
    localStorage.removeItem('authToken')
    localStorage.removeItem('refreshToken')
  }

  static setRememberMe(remember: boolean): void {
    if (remember) {
      // For remember me, we could extend token expiry or use a different storage
      localStorage.setItem('rememberMe', 'true')
    } else {
      localStorage.removeItem('rememberMe')
      // Could implement session storage instead of localStorage for temporary sessions
    }
  }

  static isRemembered(): boolean {
    return localStorage.getItem('rememberMe') === 'true'
  }
}