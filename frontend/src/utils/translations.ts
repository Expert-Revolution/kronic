export const translations = {
  en: {
    login: {
      title: 'Login to Kronic',
      subtitle: 'Enter your credentials to access the CronJob manager.',
      email: 'Email',
      emailPlaceholder: 'Enter your email',
      password: 'Password',
      passwordPlaceholder: 'Enter your password',
      rememberMe: 'Remember me',
      loginButton: 'Login',
      loggingIn: 'Logging in...',
      forgotPassword: 'Forgot password?',
      noAccount: "Don't have an account?",
      signUp: 'Sign up here',
      showPassword: 'Show password',
      hidePassword: 'Hide password'
    },
    register: {
      title: 'Create Account',
      email: 'Email',
      emailPlaceholder: 'Enter your email',
      password: 'Password',
      passwordPlaceholder: 'Create a strong password',
      confirmPassword: 'Confirm Password',
      confirmPasswordPlaceholder: 'Confirm your password',
      registerButton: 'Create Account',
      creating: 'Creating account...',
      hasAccount: 'Already have an account?',
      signIn: 'Sign in here',
      passwordHint: 'Minimum 8 characters with uppercase, lowercase, number and special character',
      close: 'Close'
    },
    validation: {
      required: 'This field is required',
      invalidEmail: 'Please enter a valid email address',
      passwordTooShort: 'Password must be at least 8 characters',
      passwordWeak: 'Password must contain uppercase, lowercase, number and special character',
      passwordsDoNotMatch: 'Passwords do not match'
    },
    errors: {
      networkError: 'Network error. Please try again.',
      loginFailed: 'Login failed',
      registrationFailed: 'Registration failed'
    },
    success: {
      accountCreated: 'Account created successfully! You can now login.'
    }
  },
  es: {
    login: {
      title: 'Iniciar sesión en Kronic',
      subtitle: 'Ingresa tus credenciales para acceder al administrador de CronJob.',
      email: 'Correo electrónico',
      emailPlaceholder: 'Ingresa tu correo electrónico',
      password: 'Contraseña',
      passwordPlaceholder: 'Ingresa tu contraseña',
      rememberMe: 'Recordarme',
      loginButton: 'Iniciar sesión',
      loggingIn: 'Iniciando sesión...',
      forgotPassword: '¿Olvidaste tu contraseña?',
      noAccount: '¿No tienes una cuenta?',
      signUp: 'Regístrate aquí',
      showPassword: 'Mostrar contraseña',
      hidePassword: 'Ocultar contraseña'
    },
    register: {
      title: 'Crear cuenta',
      email: 'Correo electrónico',
      emailPlaceholder: 'Ingresa tu correo electrónico',
      password: 'Contraseña',
      passwordPlaceholder: 'Crea una contraseña segura',
      confirmPassword: 'Confirmar contraseña',
      confirmPasswordPlaceholder: 'Confirma tu contraseña',
      registerButton: 'Crear cuenta',
      creating: 'Creando cuenta...',
      hasAccount: '¿Ya tienes una cuenta?',
      signIn: 'Inicia sesión aquí',
      passwordHint: 'Mínimo 8 caracteres con mayúscula, minúscula, número y carácter especial',
      close: 'Cerrar'
    },
    validation: {
      required: 'Este campo es obligatorio',
      invalidEmail: 'Por favor ingresa un correo electrónico válido',
      passwordTooShort: 'La contraseña debe tener al menos 8 caracteres',
      passwordWeak: 'La contraseña debe contener mayúscula, minúscula, número y carácter especial',
      passwordsDoNotMatch: 'Las contraseñas no coinciden'
    },
    errors: {
      networkError: 'Error de red. Inténtalo de nuevo.',
      loginFailed: 'Error al iniciar sesión',
      registrationFailed: 'Error al registrarse'
    },
    success: {
      accountCreated: '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.'
    }
  }
} as const

export type TranslationKey = keyof typeof translations.en
export type NestedTranslationKey<T> = T extends object 
  ? { [K in keyof T]: T[K] extends object 
      ? `${string & K}.${NestedTranslationKey<T[K]>}` 
      : string & K 
    }[keyof T]
  : never