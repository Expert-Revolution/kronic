# React Frontend for Kronic Login UI

This directory contains the modern React-based login UI for Kronic, replacing the previous AlpineJS implementation.

## Features

- **TypeScript**: Full TypeScript support with strict type checking
- **React 19**: Latest React with modern hooks and patterns
- **Form Validation**: Real-time client-side validation with proper error handling
- **Password Toggle**: Show/hide password functionality with accessibility support
- **Remember Me**: Persistent login option with localStorage integration
- **Loading States**: Proper loading indicators and disabled states during API calls
- **Error Handling**: Comprehensive error display for network and validation errors
- **Accessibility**: WCAG 2.1 compliant with proper ARIA attributes and focus management
- **Internationalization**: Multi-language support (English/Spanish) with easy extensibility
- **Responsive Design**: Mobile-first CSS with proper breakpoints and touch-friendly UI
- **Dark Mode**: Theme switching with system preference detection
- **Smooth Animations**: CSS transitions and animations with reduced motion support
- **Register Modal**: Modal-based registration form with validation

## Architecture

### Components

- **`LoginApp.tsx`**: Main application component with theme and language controls
- **`LoginForm.tsx`**: Login form with validation and submission handling
- **`RegisterModal.tsx`**: Registration modal with form validation

### Hooks

- **`useTranslation.ts`**: Internationalization hook for text translations
- **`useTheme.ts`**: Theme management hook for dark/light mode switching

### Services

- **`authService.ts`**: Authentication API service layer
- **`validation.ts`**: Form validation utilities
- **`translations.ts`**: Translation strings and language definitions

### Types

- **`auth.ts`**: TypeScript type definitions for authentication

## Development

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ with Flask backend running

### Setup

```bash
# Install dependencies
cd frontend
npm install

# Development build with hot reload
npm run dev

# Production build
npm run build
```

### Building for Production

The production build creates optimized bundles in `../static/dist/`:

```bash
npm run build
```

This generates:
- `login.js` - Minified React application bundle
- `login.css` - Compiled and optimized styles

### Development Workflow

1. **Start Flask backend**: Ensure the Flask app is running on port 5000
2. **Frontend development**: Use `npm run dev` for hot reload during development
3. **Production build**: Run `npm run build` before committing changes
4. **Test integration**: Verify the login page loads at `http://localhost:5000/login`

## Integration with Flask

The React application integrates with the existing Flask backend:

### Template Integration

The `templates/login.html` template includes:
```html
<div id="login-root"></div>
<script type="module" src="/dist/login.js"></script>
<link rel="stylesheet" href="/dist/login.css">
```

### API Integration

The React app connects to existing Flask auth endpoints:
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `GET /api/auth/check-auth` - Authentication status check

### Static File Serving

Static files are served from `/static/dist/` by Flask's static file handler.

## Customization

### Adding Languages

1. Add language to `types/auth.ts`:
```typescript
export type Language = 'en' | 'es' | 'fr'
```

2. Add translations to `utils/translations.ts`:
```typescript
export const translations = {
  // ... existing languages
  fr: {
    login: { title: 'Se connecter à Kronic', ... }
  }
}
```

3. Add language option to `LoginApp.tsx`:
```tsx
<option value="fr">🇫🇷 FR</option>
```

### Theming

Customize colors and styles in `styles/login.css`:
```css
:root {
  --primary-color: #your-color;
  --primary-dark: #your-dark-color;
  /* ... other custom properties */
}
```

### Form Validation

Extend validation rules in `utils/validation.ts`:
```typescript
export const validateCustomField = (value: string): string | undefined => {
  // Custom validation logic
}
```

## Testing

### Manual Testing

Run the test script to verify integration:
```bash
python3 ../test_react_ui.py
```

### Browser Testing

1. Start Flask: `python3 app.py` or use the main application
2. Navigate to `http://localhost:5000/login`
3. Test features:
   - Form validation (try invalid emails, short passwords)
   - Password visibility toggle
   - Remember me checkbox
   - Registration modal
   - Theme switching (dark/light)
   - Language switching (EN/ES)
   - Responsive design (resize browser)

## Deployment

For production deployment:

1. **Build the frontend**:
   ```bash
   cd frontend && npm run build
   ```

2. **Commit built assets**: The `static/dist/` files should be committed to the repository

3. **Flask serves static files**: No additional web server configuration needed

## Troubleshooting

### Common Issues

1. **React app not loading**: Check browser console for JavaScript errors
2. **Styles not applied**: Verify CSS file is loading correctly
3. **API calls failing**: Check Flask backend is running and CORS is configured
4. **Build failures**: Ensure all TypeScript types are correct

### Debug Mode

For debugging, temporarily modify the Vite config to disable minification:
```typescript
build: {
  minify: false,
  // ... other options
}
```

## Browser Support

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Mobile browsers with ES2020 support

## Performance

- **Bundle size**: ~200KB minified (includes React, styles, and application code)
- **Load time**: ~100ms on fast connections
- **Accessibility**: Screen reader compatible, keyboard navigable
- **Mobile**: Touch-friendly with responsive breakpoints