import React from 'react'
import { FaFile, FaMusic } from 'react-icons/fa'
import type { FileItem } from '@/types'

interface FilePreviewProps {
  file: FileItem
  maxWidth?: number
  maxHeight?: number
}

const isImageFile = (file: FileItem): boolean => {
  const mimeType = file.mimeType || ''
  const name = file.name.toLowerCase()
  return (
    mimeType.startsWith('image/') || name.match(/\.(jpg|jpeg|png|gif|webp|svg|bmp)$/) !== null
  )
}

const isVideoFile = (file: FileItem): boolean => {
  const mimeType = file.mimeType || ''
  const name = file.name.toLowerCase()
  return (
    mimeType.startsWith('video/') || name.match(/\.(mp4|mkv|avi|mov|flv|wmv|webm)$/) !== null
  )
}

const isAudioFile = (file: FileItem): boolean => {
  const mimeType = file.mimeType || ''
  const name = file.name.toLowerCase()
  return (
    mimeType.startsWith('audio/') || name.match(/\.(mp3|wav|flac|aac|ogg|m4a)$/) !== null
  )
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  file,
  maxWidth = 400,
  maxHeight = 300,
}) => {
  if (isImageFile(file)) {
    return (
      <div className="flex items-center justify-center bg-subtle rounded-lg overflow-hidden">
        <img
          src={file.path}
          alt={file.name}
          style={{ maxWidth: `${maxWidth}px`, maxHeight: `${maxHeight}px` }}
          className="object-contain"
          onError={(e) => {
            const img = e.target as HTMLImageElement
            img.style.display = 'none'
          }}
        />
      </div>
    )
  }

  if (isVideoFile(file)) {
    return (
      <div className="flex items-center justify-center bg-subtle rounded-lg overflow-hidden">
        <video
          src={file.path}
          style={{ maxWidth: `${maxWidth}px`, maxHeight: `${maxHeight}px` }}
          className="object-contain"
          controls
          onError={(e) => {
            const video = e.target as HTMLVideoElement
            video.style.display = 'none'
          }}
        />
      </div>
    )
  }

  if (isAudioFile(file)) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 bg-subtle rounded-lg p-6">
        <FaMusic className="w-12 h-12 text-hint" />
        <audio
          src={file.path}
          controls
          className="w-full"
          onError={(e) => {
            const audio = e.target as HTMLAudioElement
            audio.style.display = 'none'
          }}
        />
      </div>
    )
  }

  // Default file preview
  return (
    <div className="flex flex-col items-center justify-center gap-4 bg-subtle rounded-lg p-6">
      <FaFile className="w-12 h-12 text-hint" />
      <div className="text-center">
        <p className="text-sm font-medium text-dim">{file.name}</p>
        <p className="text-xs text-hint mt-1">Preview not available</p>
      </div>
    </div>
  )
}
