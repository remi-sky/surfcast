// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import SpotForecastPage from './pages/SpotForecastPage'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Home page listing spots / search form */}
        <Route path="/" element={<App />} />

        {/* 10-day detailed forecast for a spot */}
        <Route
          path="/spots/:spotId/forecast"
          element={<SpotForecastPage />}
        />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
