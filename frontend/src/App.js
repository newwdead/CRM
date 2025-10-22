import React, { useEffect, useState, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import toast, { Toaster } from 'react-hot-toast';

// Routing components
import ProtectedRoute from './components/routing/ProtectedRoute';
import MainLayout from './components/routing/MainLayout';
import NotFound from './components/routing/NotFound';
import ErrorBoundary from './components/ErrorBoundary';

// Pages - Lazy loaded for code splitting
const LoginPage = React.lazy(() => import('./components/LoginPage'));
const HomePage = React.lazy(() => import('./components/pages/HomePage'));
const ContactsPage = React.lazy(() => import('./components/pages/ContactsPage'));
const ContactPage = React.lazy(() => import('./components/pages/ContactPage'));
const OCREditorPage = React.lazy(() => import('./components/pages/OCREditorPage'));

// Other components - Lazy loaded for code splitting
const UploadCard = React.lazy(() => import('./components/UploadCard'));
const BatchUpload = React.lazy(() => import('./components/BatchUpload'));
const Companies = React.lazy(() => import('./components/Companies'));
const DuplicateFinder = React.lazy(() => import('./components/DuplicateFinder'));
const ImportExport = React.lazy(() => import('./components/ImportExport'));
const Settings = React.lazy(() => import('./components/Settings'));
const AdminPanel = React.lazy(() => import('./components/AdminPanel'));

/**
 * Scroll Restoration Component
 * Scrolls to top on route change
 */
function ScrollToTop() {
  const location = useLocation();
  
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);
  
  return null;
}

/**
 * Loading Fallback Component
 */
function LoadingFallback() {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '70vh',
      fontSize: '18px',
      color: '#666'
    }}>
      <div className="spinner" style={{ marginRight: '12px' }}></div>
      Loading...
    </div>
  );
}

/**
 * Main App Component with React Router
 */
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [lang, setLang] = useState(localStorage.getItem('lang') || 'ru');

  // Check authentication on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        setIsAuthenticated(true);
        
        // Verify token is still valid
        fetch('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        .then(response => {
          if (!response.ok) {
            handleLogout();
          }
        })
        .catch(() => {
          handleLogout();
        });
      } catch (error) {
        handleLogout();
      }
    }
    
    setAuthLoading(false);
  }, []);

  const handleLoginSuccess = (userData) => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
  };

  const toggleLanguage = () => {
    const newLang = lang === 'en' ? 'ru' : 'en';
    setLang(newLang);
    localStorage.setItem('lang', newLang);
    localStorage.setItem('language', newLang); // For compatibility
  };

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        fontSize: '18px'
      }}>
        Loading...
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <HelmetProvider>
        <BrowserRouter>
        <ScrollToTop />
        <Toaster position="top-right" />
        
        <Routes>
          {/* Login Route */}
          <Route 
            path="/login" 
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Suspense fallback={<LoadingFallback />}>
                  <LoginPage onLoginSuccess={handleLoginSuccess} lang={lang} t={{}} />
                </Suspense>
              )
            } 
          />

          {/* Protected Routes with Layout */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <MainLayout lang={lang} toggleLanguage={toggleLanguage} onLogout={handleLogout}>
                  <Suspense fallback={<LoadingFallback />}>
                    <Routes>
                      {/* Home */}
                      <Route path="/" element={<HomePage lang={lang} />} />

                      {/* Contacts */}
                      <Route path="/contacts" element={<ContactsPage lang={lang} />} />
                      <Route path="/contacts/:id" element={<ContactPage lang={lang} />} />
                      <Route path="/contacts/:id/ocr-editor" element={<OCREditorPage lang={lang} />} />

                      {/* Organizations */}
                      <Route path="/companies" element={<Companies lang={lang} />} />

                      {/* Duplicates */}
                      <Route path="/duplicates" element={<DuplicateFinder lang={lang} />} />

                      {/* Upload */}
                      <Route path="/upload" element={<UploadCard t={{}} lang={lang} />} />

                      {/* Batch Upload */}
                      <Route path="/batch-upload" element={<BatchUpload lang={lang} />} />

                      {/* Import/Export */}
                      <Route path="/import-export" element={<ImportExport t={{}} lang={lang} />} />

                      {/* Settings */}
                      <Route path="/settings" element={<Settings t={{}} lang={lang} />} />

                      {/* Admin Panel (Protected) */}
                      <Route 
                        path="/admin/*" 
                        element={
                          <ProtectedRoute requireAdmin={true}>
                            <AdminPanel t={{}} lang={lang} />
                          </ProtectedRoute>
                        } 
                      />

                      {/* 404 Not Found */}
                      <Route path="*" element={<NotFound lang={lang} />} />
                    </Routes>
                  </Suspense>
                </MainLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
        </BrowserRouter>
      </HelmetProvider>
    </ErrorBoundary>
  );
}

export default App;
