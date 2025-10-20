import React from 'react';
import { motion } from 'framer-motion';

// Skeleton для таблицы контактов
export function ContactListSkeleton({ rows = 5 }) {
  return (
    <div style={{ padding: '20px' }}>
      {/* Search skeleton */}
      <div style={{ 
        marginBottom: '20px', 
        display: 'flex', 
        gap: '12px',
        flexWrap: 'wrap'
      }}>
        <SkeletonBox width="250px" height="40px" />
        <SkeletonBox width="150px" height="40px" />
        <SkeletonBox width="150px" height="40px" />
      </div>

      {/* Table skeleton */}
      <div style={{ 
        border: '1px solid var(--border-color)', 
        borderRadius: 'var(--radius)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{ 
          display: 'flex', 
          gap: '12px', 
          padding: '16px',
          background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-color)'
        }}>
          <SkeletonBox width="30px" height="20px" />
          <SkeletonBox width="40px" height="20px" />
          <SkeletonBox width="80px" height="20px" />
          <SkeletonBox width="120px" height="20px" />
          <SkeletonBox width="100px" height="20px" />
          <SkeletonBox width="100px" height="20px" />
        </div>

        {/* Rows */}
        {Array.from({ length: rows }).map((_, index) => (
          <div 
            key={index}
            style={{ 
              display: 'flex', 
              gap: '12px', 
              padding: '16px',
              borderBottom: index < rows - 1 ? '1px solid var(--border-color)' : 'none'
            }}
          >
            <SkeletonBox width="30px" height="20px" />
            <SkeletonBox width="40px" height="20px" />
            <SkeletonBox width="80px" height="20px" />
            <SkeletonBox width="120px" height="20px" />
            <SkeletonBox width="100px" height="20px" />
            <SkeletonBox width="100px" height="20px" />
            <SkeletonBox width="60px" height="30px" />
          </div>
        ))}
      </div>

      {/* Pagination skeleton */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        gap: '8px', 
        marginTop: '20px' 
      }}>
        <SkeletonBox width="80px" height="36px" />
        <SkeletonBox width="40px" height="36px" />
        <SkeletonBox width="40px" height="36px" />
        <SkeletonBox width="40px" height="36px" />
        <SkeletonBox width="80px" height="36px" />
      </div>
    </div>
  );
}

// Skeleton для карточки контакта
export function ContactCardSkeleton() {
  return (
    <div className="modal-overlay">
      <div className="modal contact-card-modal">
        <div style={{ padding: '20px' }}>
          {/* Header */}
          <div style={{ marginBottom: '24px' }}>
            <SkeletonBox width="200px" height="32px" style={{ marginBottom: '8px' }} />
            <SkeletonBox width="150px" height="20px" />
          </div>

          {/* Sections */}
          {[1, 2, 3].map((section) => (
            <div key={section} style={{ marginBottom: '24px' }}>
              <SkeletonBox width="180px" height="24px" style={{ marginBottom: '12px' }} />
              <div style={{ display: 'grid', gap: '12px' }}>
                <SkeletonBox width="100%" height="20px" />
                <SkeletonBox width="100%" height="20px" />
                <SkeletonBox width="80%" height="20px" />
              </div>
            </div>
          ))}

          {/* Buttons */}
          <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
            <SkeletonBox width="100px" height="40px" />
            <SkeletonBox width="100px" height="40px" />
          </div>
        </div>
      </div>
    </div>
  );
}

// Базовый компонент Skeleton Box с анимацией
export function SkeletonBox({ width = '100px', height = '20px', style = {} }) {
  return (
    <motion.div
      animate={{
        opacity: [0.5, 1, 0.5],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: "easeInOut"
      }}
      style={{
        width,
        height,
        background: 'linear-gradient(90deg, var(--bg-secondary) 25%, var(--border-color) 50%, var(--bg-secondary) 75%)',
        backgroundSize: '200% 100%',
        borderRadius: '4px',
        ...style
      }}
    />
  );
}

// Skeleton для списка компаний
export function CompaniesSkeleton({ count = 5 }) {
  return (
    <div style={{ padding: '20px' }}>
      <SkeletonBox width="200px" height="32px" style={{ marginBottom: '24px' }} />
      
      {Array.from({ length: count }).map((_, index) => (
        <div 
          key={index}
          style={{ 
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius)',
            padding: '16px',
            marginBottom: '12px'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <SkeletonBox width="180px" height="24px" />
            <SkeletonBox width="24px" height="24px" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Skeleton для карточки загрузки
export function UploadCardSkeleton() {
  return (
    <div className="card">
      <SkeletonBox width="200px" height="28px" style={{ marginBottom: '20px' }} />
      
      {/* Drop zone skeleton */}
      <div style={{ 
        border: '2px dashed var(--border-color)', 
        borderRadius: 'var(--radius)',
        padding: '40px',
        textAlign: 'center',
        marginBottom: '20px'
      }}>
        <SkeletonBox width="60px" height="60px" style={{ margin: '0 auto 12px' }} />
        <SkeletonBox width="200px" height="20px" style={{ margin: '0 auto' }} />
      </div>

      <SkeletonBox width="100%" height="40px" style={{ marginBottom: '12px' }} />
      <SkeletonBox width="100%" height="48px" />
    </div>
  );
}

export default {
  ContactListSkeleton,
  ContactCardSkeleton,
  CompaniesSkeleton,
  UploadCardSkeleton,
  SkeletonBox
};

