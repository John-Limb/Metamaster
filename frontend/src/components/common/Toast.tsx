import React, { useEffect, useState } from 'react'
import { FaCheckCircle, FaExclamationCircle, FaInfoCircle, FaTimesCircle, FaTimes } from 'react-icons/fa'
import type { Toast as ToastType } from '@/types'

export interface ToastProps extends Omit<ToastType, 'id'> {
  id?: string
  onClose?: () => void
}

export const Toast: React.FC<ToastProps> = ({
  id: _id, // eslint-disable-line @typescript-eslint/no-unused-vars
  type = 'info',
  message,
  duration = 5000,
  onClose,
}) => {
  const [isExiting, setIsExiting] = useState(false)

  const handleClose = () => {
    setIsExiting(true)
    setTimeout(() => {
      onClose?.()
    }, 200)
  }

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose()
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [duration])

  const typeConfig = {
    success: {
      bgColor: 'bg-success-50 dark:bg-success-900/20',
      borderColor: 'border-success-200 dark:border-success-800',
      textColor: 'text-success-800 dark:text-success-200',
      icon: <FaCheckCircle className="w-5 h-5 text-success-500" />,
    },
    error: {
      bgColor: 'bg-danger-50 dark:bg-danger-900/20',
      borderColor: 'border-danger-200 dark:border-danger-800',
      textColor: 'text-danger-800 dark:text-danger-200',
      icon: <FaTimesCircle className="w-5 h-5 text-danger-500" />,
    },
    warning: {
      bgColor: 'bg-warning-50 dark:bg-warning-900/20',
      borderColor: 'border-warning-200 dark:border-warning-800',
      textColor: 'text-warning-800 dark:text-warning-200',
      icon: <FaExclamationCircle className="w-5 h-5 text-warning-500" />,
    },
    info: {
      bgColor: 'bg-info-50 dark:bg-info-900/20',
      borderColor: 'border-info-200 dark:border-info-800',
      textColor: 'text-info-800 dark:text-info-200',
      icon: <FaInfoCircle className="w-5 h-5 text-info-500" />,
    },
  }

  const config = typeConfig[type]

  return (
    <div
      className={`
        ${config.bgColor} ${config.borderColor} ${config.textColor}
        border rounded-lg p-4 flex items-start gap-3 shadow-lg
        animate-toast-in-bottom
        ${isExiting ? 'animate-toast-out-bottom' : ''}
        transition-all duration-200
        max-w-md
      `}
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="flex-shrink-0 mt-0.5">{config.icon}</div>
      <div className="flex-1">
        <p className="text-sm font-medium">{message}</p>
      </div>
      <button
        onClick={handleClose}
        className={`${config.textColor} hover:opacity-70 transition flex-shrink-0 p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/10`}
        aria-label="Close notification"
        type="button"
      >
        <FaTimes className="w-4 h-4" />
      </button>
    </div>
  )
}

interface ToastContainerProps {
  toasts: ToastType[]
  onRemoveToast: (id: string) => void
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemoveToast }) => {
  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-md w-full pointer-events-none"
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast
            {...toast}
            id={toast.id}
            onClose={() => onRemoveToast(toast.id)}
          />
        </div>
      ))}
    </div>
  )
}

export default Toast
