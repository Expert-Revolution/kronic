
# COPILOT INSTRUCTIONS FOR KRONIC

## PROJECT OVERVIEW

Kronic is a web-based Kubernetes CronJob management UI built with Flask, AlpineJS, and PicoCSS. It provides a simple interface for viewing, editing, triggering, and managing CronJobs across Kubernetes clusters.

**Key Architecture:**
- **Backend**: Flask app (`app.py`, `app/main.py`) with Kubernetes client integration (`kron.py`)
- **Authentication**: Multi-layered (JWT, Basic Auth, PostgreSQL users) in `auth_api.py`, `jwt_auth.py`
- **Frontend**: Server-rendered templates with AlpineJS + modern React components in `frontend/`
- **Deployment**: Docker containers, Helm charts, k3d for local development

## DEVELOPMENT WORKFLOW

### Local Development Setup
```bash
# Quick start with automated k3d cluster
./scripts/dev.sh up          # Starts k3d + postgres + kronic
./scripts/dev.sh logs        # View application logs  
./scripts/dev.sh down        # Clean shutdown

# Manual development against existing cluster
docker-compose up postgres   # Start database only
python app.py               # Run Flask directly (port 5000)
```

### Testing Strategy
```bash
# Unit tests (fast, no dependencies)
pytest tests/ -m "not integration"

# Integration tests (uses ephemeral kind clusters)  
pytest tests/ -m "integration"

# Test coverage
pytest --cov=. tests/
```

## PROJECT-SPECIFIC PATTERNS

### Kubernetes Integration (`kron.py`)
- **Client Setup**: Auto-detects in-cluster vs kubeconfig authentication
- **Core Functions**: `get_cronjobs()`, `get_cronjob()`, `trigger_cronjob()`, `toggle_cronjob_suspend()`
- **Namespace Filtering**: Decorator-based access control via `config.ALLOW_NAMESPACES`
- **Error Handling**: Returns `{"error": code, "exception": details}` on failures

### Authentication Architecture
- **Multi-tier**: JWT cookies → Database users → Environment variables (fallback)
- **Database Mode**: PostgreSQL with Alembic migrations (`alembic upgrade head`)
- **Namespace Security**: `@namespace_filter` decorator enforces access controls
- **Session Management**: `verify_password()` in `app.py` handles all auth methods

### Configuration Patterns (`config.py`)
- **Environment Variables**: `KRONIC_*` prefix for all settings
- **Database Toggle**: `DATABASE_ENABLED` flag switches auth modes
- **Namespace Modes**: `ALLOW_NAMESPACES` (list) vs `NAMESPACE_ONLY` (single)
- **Test Mode**: `KRONIC_TEST=true` disables Kubernetes client initialization

### Route Organization
- **Legacy Routes**: `app.py` (being migrated to `app/main.py`)
- **API Endpoints**: `/api/namespaces/<ns>/cronjobs/<name>` pattern
- **Template Routes**: Server-rendered HTML with YAML editing capabilities
- **YAML Validation**: `_validate_cronjob_yaml()` with syntax + semantic checks

## DEPLOYMENT & INFRASTRUCTURE

### Helm Chart (`chart/kronic/`)
- **Versioning**: Semantic versioning with `./scripts/bump-chart-version.sh`
- **Authentication**: Built-in basic auth with random password generation
- **Network Policy**: Optional ingress controls via `networkPolicy.enabled`
- **Database Support**: PostgreSQL backend configuration

### Development Scripts
- **`scripts/dev.sh`**: Complete local environment with k3d cluster
- **`scripts/run-tests.sh`**: Standardized test execution 
- **`scripts/seed_database.py`**: Initialize users and roles

---

## OPERATIONAL GUIDELINES & PRIME DIRECTIVE

**Avoid working on more than one file at a time.** Multiple simultaneous edits to a file will cause corruption.
**Be chatting and teach about what you are doing while coding.**

### MANDATORY PLANNING PHASE

When working with large files (>300 lines) or complex changes:
    1. ALWAYS start by creating a detailed plan BEFORE making any edits
    2. Your plan MUST include:
           - All functions/sections that need modification
           - The order in which changes should be applied
           - Dependencies between changes
           - Estimated number of separate edits required

    3. Format your plan as:

## PROPOSED EDIT PLAN

    Working with: [filename]
    Total planned edits: [number]

### MAKING EDITS

    - Focus on one conceptual change at a time
    - Show clear "before" and "after" snippets when proposing changes
    - Include concise explanations of what changed and why
    - Always check if the edit maintains the project's coding style

### Edit sequence:

    1. [First specific change] - Purpose: [why]
    2. [Second specific change] - Purpose: [why]
    3. Do you approve this plan? I'll proceed with Edit [number] after your confirmation.
    4. WAIT for explicit user confirmation before making ANY edits when user ok edit [number]

### EXECUTION PHASE

    - After each individual edit, clearly indicate progress:
        "✅ Completed edit [#] of [total]. Ready for next edit?"
    - If you discover additional needed changes during editing:
    - STOP and update the plan
    - Get approval before continuing

### REFACTORING GUIDANCE

    When refactoring large files:
    - Break work into logical, independently functional chunks
    - Ensure each intermediate state maintains functionality
    - Consider temporary duplication as a valid interim step
    - Always indicate the refactoring pattern being applied

### RATE LIMIT AVOIDANCE

    - For very large files, suggest splitting changes across multiple sessions
    - Prioritize changes that are logically complete units
    - Always provide clear stopping points

---

### MANDATORY PLANNING PHASE

    When working with large files (>300 lines) or complex changes:
        1. ALWAYS start by creating a detailed plan BEFORE making any edits
            2. Your plan MUST include:
                   - All functions/sections that need modification
                   - The order in which changes should be applied
                   - Dependencies between changes
                   - Estimated number of separate edits required

            3. Format your plan as:

## PROPOSED EDIT PLAN

    Working with: [filename]
    Total planned edits: [number]

### MAKING EDITS

    - Focus on one conceptual change at a time
    - Show clear "before" and "after" snippets when proposing changes
    - Include concise explanations of what changed and why
    - Always check if the edit maintains the project's coding style

### Edit sequence:

    1. [First specific change] - Purpose: [why]
    2. [Second specific change] - Purpose: [why]
    3. Do you approve this plan? I'll proceed with Edit [number] after your confirmation.
    4. WAIT for explicit user confirmation before making ANY edits when user ok edit [number]

### EXECUTION PHASE

    - After each individual edit, clearly indicate progress:
        "✅ Completed edit [#] of [total]. Ready for next edit?"
    - If you discover additional needed changes during editing:
    - STOP and update the plan
    - Get approval before continuing

### REFACTORING GUIDANCE

    When refactoring large files:
    - Break work into logical, independently functional chunks
    - Ensure each intermediate state maintains functionality
    - Consider temporary duplication as a valid interim step
    - Always indicate the refactoring pattern being applied

### RATE LIMIT AVOIDANCE

    - For very large files, suggest splitting changes across multiple sessions
    - Prioritize changes that are logically complete units
    - Always provide clear stopping points

## General Requirements

    Use modern technologies as described below for all code suggestions. Prioritize clean, maintainable code with appropriate comments.
    - @azure Rule - Use Azure Best Practices: When generating code for Azure, running terminal commands for Azure, or performing operations related to Azure, invoke your `get_azure_best_practices` tool if available.

### Accessibility

    - Ensure compliance with **WCAG 2.1** AA level minimum, AAA whenever feasible.
    - Always suggest:
    - Labels for form fields.
    - Proper **ARIA** roles and attributes.
    - Adequate color contrast.
    - Alternative texts (`alt`, `aria-label`) for media elements.
    - Semantic HTML for clear structure.
    - Tools like **Lighthouse** for audits.

## Browser Compatibility

    - Prioritize feature detection (`if ('fetch' in window)` etc.).
    - Support latest two stable releases of major browsers:
    - Firefox, Chrome, Edge, Safari (macOS/iOS)
    - Emphasize progressive enhancement with polyfills or bundlers (e.g., **Babel**, **Vite**) as needed.

## HTML/CSS Requirements

    - **HTML**:
    - Use HTML5 semantic elements (`<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`, `<search>`, etc.)
    - Include appropriate ARIA attributes for accessibility
    - Ensure valid markup that passes W3C validation
    - Use responsive design practices
    - Optimize images using modern formats (`WebP`, `AVIF`)
    - Include `loading="lazy"` on images where applicable
    - Generate `srcset` and `sizes` attributes for responsive images when relevant
    - Prioritize SEO-friendly elements (`<title>`, `<meta description>`, Open Graph tags)

    - **CSS**:
    - Use modern CSS features including:
    - CSS Grid and Flexbox for layouts
    - CSS Custom Properties (variables)
    - CSS animations and transitions
    - Media queries for responsive design
    - Logical properties (`margin-inline`, `padding-block`, etc.)
    - Modern selectors (`:is()`, `:where()`, `:has()`)
    - Follow BEM or similar methodology for class naming
    - Use CSS nesting where appropriate
    - Include dark mode support with `prefers-color-scheme`
    - Prioritize modern, performant fonts and variable fonts for smaller file sizes
    - Use modern units (`rem`, `vh`, `vw`) instead of traditional pixels (`px`) for better responsiveness

## JavaScript Requirements

    - **Minimum Compatibility**: ECMAScript 2020 (ES11) or higher
    - **Features to Use**:
    - Arrow functions
    - Template literals
    - Destructuring assignment
    - Spread/rest operators
    - Async/await for asynchronous code
    - Classes with proper inheritance when OOP is needed
    - Object shorthand notation
    - Optional chaining (`?.`)
    - Nullish coalescing (`??`)
    - Dynamic imports
    - BigInt for large integers
    - `Promise.allSettled()`
    - `String.prototype.matchAll()`
    - `globalThis` object
    - Private class fields and methods
    - Export * as namespace syntax
    - Array methods (`map`, `filter`, `reduce`, `flatMap`, etc.)
    - **Avoid**:
    - `var` keyword (use `const` and `let`)
    - jQuery or any external libraries
    - Callback-based asynchronous patterns when promises can be used
    - Internet Explorer compatibility
    - Legacy module formats (use ES modules)
    - Limit use of `eval()` due to security risks
    - **Performance Considerations:**
    - Recommend code splitting and dynamic imports for lazy loading
    **Error Handling**:
    - Use `try-catch` blocks **consistently** for asynchronous and API calls, and handle promise rejections explicitly.
    - Differentiate among:
    - **Network errors** (e.g., timeouts, server errors, rate-limiting)
    - **Functional/business logic errors** (logical missteps, invalid user input, validation failures)
    - **Runtime exceptions** (unexpected errors such as null references)
    - Provide **user-friendly** error messages (e.g., “Something went wrong. Please try again shortly.”) and log more technical details to dev/ops (e.g., via a logging service).
    - Consider a central error handler function or global event (e.g., `window.addEventListener('unhandledrejection')`) to consolidate reporting.
    - Carefully handle and validate JSON responses, incorrect HTTP status codes, etc.

## Documentation Requirements

    - Include JSDoc comments for JavaScript/TypeScript.
    - Document complex functions with clear examples.
    - Maintain concise Markdown documentation.
    - Minimum docblock info: `param`, `return`, `throws`, `author`

## Security Considerations

    - Sanitize all user inputs thoroughly.
    - Parameterize database queries.
    - Enforce strong Content Security Policies (CSP).
    - Use CSRF protection where applicable.
    - Ensure secure cookies (`HttpOnly`, `Secure`, `SameSite=Strict`).
    - Limit privileges and enforce role-based access control.
    - Implement detailed internal logging and monitoring.
