import React from 'react'
import ReactDOM from 'react-dom/client'
import LoginApp from './components/LoginApp'
import './styles/login.css'

const root = ReactDOM.createRoot(document.getElementById('login-root')!)
root.render(
  <React.StrictMode>
    <LoginApp />
  </React.StrictMode>
)