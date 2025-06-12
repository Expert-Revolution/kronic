#!/usr/bin/env python3
"""
Test script to verify React login UI is working correctly using Flask test client.
"""

import os
import sys
import pytest

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
config.TEST = True

from app import app


def test_react_login_ui():
    """Test that the React login UI loads and functions correctly."""
    
    with app.test_client() as client:
        # Test 1: Basic template loading
        response = client.get('/login')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        html_content = response.data.decode('utf-8')
        assert 'login-root' in html_content, "React mount point not found"
        assert '/dist/login.js' in html_content, "React JS bundle not found"
        assert '/dist/login.css' in html_content, "React CSS bundle not found"
        
        # Test 2: Static files accessibility
        js_response = client.get('/dist/login.js')
        css_response = client.get('/dist/login.css')
        
        assert js_response.status_code == 200, f"JS bundle not accessible: {js_response.status_code}"
        assert css_response.status_code == 200, f"CSS bundle not accessible: {css_response.status_code}"
        
        # Check for React content in JS bundle
        js_content = js_response.data.decode('utf-8')
        css_content = css_response.data.decode('utf-8')
        
        assert 'React' in js_content, "React library not found in JS bundle"
        assert 'login' in css_content, "Login styles not found in CSS bundle"
        
        # Test 3: API endpoints
        # Test login endpoint exists
        login_response = client.post('/api/auth/login', 
                                   json={'email': 'test@example.com', 'password': 'invalid'})
        # Should return 400 or 401, not 404
        assert login_response.status_code != 404, "Login API endpoint not found"
        
        # Test register endpoint exists (if enabled)
        register_response = client.post('/api/auth/register',
                                      json={'email': 'test@example.com', 'password': 'invalid'})
        # Should return 400 or similar, not 404 (or might be disabled)
        assert register_response.status_code in [400, 401, 403, 405, 501], f"Unexpected register response: {register_response.status_code}"
        
        # Test 4: React Features
        # Check for specific React component indicators in the JS bundle
        react_indicators = [
            'react',  # React library reference
            'jsx',    # JSX runtime
            'login-root',  # Our mount point
            'email',  # Form field names
            'password'
        ]
        
        css_indicators = [
            'login-container',  # Our main CSS classes
            'login-card',
            'form-input',
            'btn-primary'
        ]
        
        missing_js = [indicator for indicator in react_indicators if indicator.lower() not in js_content.lower()]
        missing_css = [indicator for indicator in css_indicators if indicator not in css_content]
        
        # Allow some missing indicators as the build might optimize them out
        assert len(missing_js) <= 2, f"Too many missing React indicators in JS: {missing_js}"
        assert len(missing_css) <= 2, f"Too many missing CSS indicators: {missing_css}"


if __name__ == "__main__":
    pytest.main([__file__])