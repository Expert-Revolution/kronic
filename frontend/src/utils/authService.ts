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
      credentials: 'include', // Include cookies in request
      body: JSON.stringify({
        email: formData.email,
        password: formData.password
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new AuthError(data.error || 'Login failed')
    }

    // Tokens are now handled via HTTP-only cookies
    // No need to store them in localStorage
    return data
  }

  static async register(formData: RegisterFormData): Promise<void> {
    const response = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include', // Include cookies in request
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
    const response = await fetch(`${API_BASE}/check-auth`, {
      credentials: 'include' // Include cookies (JWT tokens) in request
    })

    if (!response.ok) {
      return { authenticated: false }
    }

    const data = await response.json()
    return data
  }

  static async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE}/logout`, {
        method: 'POST',
        credentials: 'include' // Include cookies in request
      })
    } catch (error) {
      // Even if logout fails on server, clear client state
      console.warn('Logout request failed:', error)
    }
    
    // Clear any client-side state
    this.clearClientState()
  }

  static clearClientState(): void {
    // Clear remember me state and redirect to login
    localStorage.removeItem('rememberMe')
  }

  static setRememberMe(remember: boolean): void {
    if (remember) {
      localStorage.setItem('rememberMe', 'true')
    } else {
      localStorage.removeItem('rememberMe')
    }
  }

  static isRemembered(): boolean {
    return localStorage.getItem('rememberMe') === 'true'
  }

  // Deprecated methods - kept for compatibility but no longer needed with HTTP-only cookies
  static storeTokens(token: string, refreshToken: string): void {
    // No-op: tokens are now stored as HTTP-only cookies
  }

  static getToken(): string | null {
    // No longer accessible from client-side due to HTTP-only cookies
    return null
  }

  static getRefreshToken(): string | null {
    // No longer accessible from client-side due to HTTP-only cookies
    return null
  }

  static clearTokens(): void {
    // No-op: tokens are cleared via logout endpoint
  }
}