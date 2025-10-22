import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Camera Scanner Component
 * Direct camera access for scanning business cards
 * 
 * Features:
 * - Camera preview
 * - Photo capture
 * - Flash control
 * - Camera switch (front/back)
 * - Auto-focus guide
 */
function CameraScanner({ onCapture, onClose, lang = 'ru' }) {
  const [stream, setStream] = useState(null);
  const [hasFlash, setHasFlash] = useState(false);
  const [flashOn, setFlashOn] = useState(false);
  const [facingMode, setFacingMode] = useState('environment'); // 'user' or 'environment'
  const [error, setError] = useState(null);
  const [capturing, setCapturing] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const t = {
    en: {
      capture: 'Capture',
      retake: 'Retake',
      use: 'Use Photo',
      flash: 'Flash',
      switchCamera: 'Switch Camera',
      close: 'Close',
      noCameraAccess: 'Camera access denied',
      noCameraFound: 'No camera found',
      alignCard: 'Align business card in frame'
    },
    ru: {
      capture: 'Снять',
      retake: 'Переснять',
      use: 'Использовать',
      flash: 'Вспышка',
      switchCamera: 'Переключить камеру',
      close: 'Закрыть',
      noCameraAccess: 'Нет доступа к камере',
      noCameraFound: 'Камера не найдена',
      alignCard: 'Выровняйте визитку в кадре'
    }
  }[lang];

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, [facingMode]);

  const startCamera = async () => {
    try {
      const constraints = {
        video: {
          facingMode: facingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }

      // Check if device has flash
      const track = mediaStream.getVideoTracks()[0];
      const capabilities = track.getCapabilities();
      setHasFlash(capabilities.torch === true);

    } catch (err) {
      console.error('Camera error:', err);
      setError(err.name === 'NotAllowedError' ? t.noCameraAccess : t.noCameraFound);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
  };

  const toggleFlash = async () => {
    if (!hasFlash || !stream) return;

    const track = stream.getVideoTracks()[0];
    try {
      await track.applyConstraints({
        advanced: [{ torch: !flashOn }]
      });
      setFlashOn(!flashOn);
    } catch (err) {
      console.error('Flash error:', err);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    setCapturing(true);

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to blob
    canvas.toBlob((blob) => {
      if (blob && onCapture) {
        onCapture(blob);
      }
      setCapturing(false);
    }, 'image/jpeg', 0.95);
  };

  const switchCameraFacing = () => {
    setFacingMode(facingMode === 'environment' ? 'user' : 'environment');
  };

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.9)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          color: 'white',
          padding: '20px',
          textAlign: 'center'
        }}
      >
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>📷</div>
        <h2 style={{ marginBottom: '12px' }}>{error}</h2>
        <button
          onClick={onClose}
          style={{
            marginTop: '20px',
            padding: '12px 24px',
            background: 'white',
            color: 'black',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            cursor: 'pointer'
          }}
        >
          {t.close}
        </button>
      </motion.div>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'black',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Video Preview */}
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
          />

          {/* Guide Overlay */}
          <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none'
          }}>
            <div style={{
              width: '90%',
              maxWidth: '400px',
              aspectRatio: '1.6/1',
              border: '3px solid rgba(255,255,255,0.7)',
              borderRadius: '12px',
              boxShadow: '0 0 0 9999px rgba(0,0,0,0.5)'
            }} />
            <div style={{
              position: 'absolute',
              bottom: '20px',
              left: 0,
              right: 0,
              textAlign: 'center',
              color: 'white',
              fontSize: '14px',
              textShadow: '0 2px 4px rgba(0,0,0,0.8)'
            }}>
              {t.alignCard}
            </div>
          </div>

          {/* Top Controls */}
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            padding: '20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'linear-gradient(180deg, rgba(0,0,0,0.5) 0%, transparent 100%)'
          }}>
            <button
              onClick={onClose}
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.3)',
                border: 'none',
                color: 'white',
                fontSize: '20px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              ✕
            </button>

            {hasFlash && (
              <button
                onClick={toggleFlash}
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: flashOn ? 'rgba(255,255,0,0.5)' : 'rgba(255,255,255,0.3)',
                  border: 'none',
                  color: 'white',
                  fontSize: '20px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ⚡
              </button>
            )}
          </div>
        </div>

        {/* Bottom Controls */}
        <div style={{
          padding: '20px',
          background: 'black',
          display: 'flex',
          justifyContent: 'space-around',
          alignItems: 'center',
          paddingBottom: 'calc(20px + env(safe-area-inset-bottom))'
        }}>
          {/* Switch Camera */}
          <button
            onClick={switchCameraFacing}
            style={{
              width: '50px',
              height: '50px',
              borderRadius: '50%',
              background: 'rgba(255,255,255,0.3)',
              border: 'none',
              color: 'white',
              fontSize: '24px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            🔄
          </button>

          {/* Capture Button */}
          <motion.button
            onClick={capturePhoto}
            disabled={capturing}
            whileTap={{ scale: 0.9 }}
            style={{
              width: '70px',
              height: '70px',
              borderRadius: '50%',
              background: 'white',
              border: '4px solid rgba(255,255,255,0.5)',
              cursor: 'pointer',
              position: 'relative',
              opacity: capturing ? 0.5 : 1
            }}
          >
            {capturing && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                style={{
                  position: 'absolute',
                  inset: 4,
                  border: '3px solid transparent',
                  borderTopColor: '#2563eb',
                  borderRadius: '50%'
                }}
              />
            )}
          </motion.button>

          {/* Placeholder for symmetry */}
          <div style={{ width: '50px', height: '50px' }} />
        </div>

        {/* Hidden canvas for capture */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </motion.div>
    </AnimatePresence>
  );
}

export default CameraScanner;

