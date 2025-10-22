import React from 'react';

/**
 * Error Boundary Component
 * Catches JavaScript errors anywhere in child component tree and displays fallback UI.
 * 
 * Usage:
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    // Update state with error info
    this.setState({
      error,
      errorInfo,
      errorCount: this.state.errorCount + 1
    });

    // Send to logging service (optional)
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f7fafc',
          padding: '20px'
        }}>
          <div style={{
            maxWidth: '600px',
            width: '100%',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            padding: '40px',
            textAlign: 'center'
          }}>
            {/* Error Icon */}
            <div style={{
              fontSize: '64px',
              marginBottom: '20px'
            }}>
              ⚠️
            </div>

            {/* Title */}
            <h1 style={{
              fontSize: '24px',
              fontWeight: 'bold',
              color: '#1a202c',
              marginBottom: '16px'
            }}>
              Что-то пошло не так
            </h1>

            {/* Description */}
            <p style={{
              fontSize: '16px',
              color: '#718096',
              marginBottom: '24px',
              lineHeight: '1.6'
            }}>
              Произошла непредвиденная ошибка. Пожалуйста, попробуйте перезагрузить
              страницу или обратитесь в поддержку, если проблема повторяется.
            </p>

            {/* Error Details (Development only) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details style={{
                marginBottom: '24px',
                textAlign: 'left',
                backgroundColor: '#f7fafc',
                padding: '16px',
                borderRadius: '8px',
                fontSize: '14px',
                color: '#4a5568',
                cursor: 'pointer'
              }}>
                <summary style={{ fontWeight: '600', marginBottom: '8px' }}>
                  Детали ошибки (только для разработки)
                </summary>
                <div style={{
                  marginTop: '12px',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  <strong>Error:</strong> {this.state.error.toString()}
                  <br /><br />
                  <strong>Stack:</strong>
                  <br />
                  {this.state.errorInfo && this.state.errorInfo.componentStack}
                </div>
              </details>
            )}

            {/* Error Count */}
            {this.state.errorCount > 1 && (
              <div style={{
                backgroundColor: '#fff5f5',
                color: '#c53030',
                padding: '12px',
                borderRadius: '8px',
                marginBottom: '24px',
                fontSize: '14px'
              }}>
                ⚠️ Ошибка повторилась {this.state.errorCount} раз(а)
              </div>
            )}

            {/* Action Buttons */}
            <div style={{
              display: 'flex',
              gap: '12px',
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              {/* Try Again Button */}
              <button
                onClick={this.handleReset}
                style={{
                  backgroundColor: '#4299e1',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#3182ce'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#4299e1'}
              >
                Попробовать снова
              </button>

              {/* Reload Page Button */}
              <button
                onClick={this.handleReload}
                style={{
                  backgroundColor: '#48bb78',
                  color: 'white',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#38a169'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#48bb78'}
              >
                Перезагрузить страницу
              </button>

              {/* Go Home Button */}
              <button
                onClick={() => window.location.href = '/'}
                style={{
                  backgroundColor: '#cbd5e0',
                  color: '#2d3748',
                  border: 'none',
                  padding: '12px 24px',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#a0aec0'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#cbd5e0'}
              >
                На главную
              </button>
            </div>

            {/* Help Link */}
            <div style={{
              marginTop: '24px',
              fontSize: '14px',
              color: '#718096'
            }}>
              Нужна помощь?{' '}
              <a
                href="/support"
                style={{
                  color: '#4299e1',
                  textDecoration: 'none',
                  fontWeight: '600'
                }}
              >
                Связаться с поддержкой
              </a>
            </div>
          </div>
        </div>
      );
    }

    // No error, render children
    return this.props.children;
  }
}

export default ErrorBoundary;

