import React from 'react'

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

export const Dialog: React.FC<DialogProps> = ({ open, children }) => {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div
        className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  )
}

interface DialogContentProps {
  children: React.ReactNode
  onClose?: () => void
}

export const DialogContent: React.FC<DialogContentProps> = ({ children, onClose }) => (
  <div className="p-6">
    <div className="flex justify-between items-center mb-4">
      <button
        onClick={onClose}
        className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
      >
        ×
      </button>
    </div>
    {children}
  </div>
)

interface DialogHeaderProps {
  children: React.ReactNode
}

export const DialogHeader: React.FC<DialogHeaderProps> = ({ children }) => (
  <div className="mb-4">{children}</div>
)

interface DialogTitleProps {
  children: React.ReactNode
}

export const DialogTitle: React.FC<DialogTitleProps> = ({ children }) => (
  <h2 className="text-lg font-semibold">{children}</h2>
)

interface DialogFooterProps {
  children: React.ReactNode
}

export const DialogFooter: React.FC<DialogFooterProps> = ({ children }) => (
  <div className="flex gap-3 justify-end mt-6 pt-4 border-t">{children}</div>
)
