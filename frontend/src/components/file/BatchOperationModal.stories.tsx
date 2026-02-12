import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { BatchOperationModal } from './BatchOperationModal';
import type { FileItem } from '@/types';

const meta = {
  title: 'File/BatchOperationModal',
  component: BatchOperationModal,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  argTypes: {
    operation: { control: 'select', options: ['delete', 'move', 'rename'] },
  },
  args: {
    onClose: fn(),
    onComplete: fn(),
  },
} satisfies Meta<typeof BatchOperationModal>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleFiles: FileItem[] = [
  {
    id: '1',
    name: 'The Matrix (1999).mkv',
    path: '/movies/sci-fi/the-matrix.mkv',
    type: 'file',
    size: 7.5 * 1024 * 1024 * 1024,
    mimeType: 'video/x-matroska',
    createdAt: '2024-01-01T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    name: 'Inception (2010).mkv',
    path: '/movies/sci-fi/inception.mkv',
    type: 'file',
    size: 8.2 * 1024 * 1024 * 1024,
    mimeType: 'video/x-matroska',
    createdAt: '2024-01-01T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
  },
  {
    id: '3',
    name: 'Interstellar (2014).mkv',
    path: '/movies/sci-fi/interstellar.mkv',
    type: 'file',
    size: 12.1 * 1024 * 1024 * 1024,
    mimeType: 'video/x-matroska',
    createdAt: '2024-01-01T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
  },
];

const singleFile: FileItem[] = [sampleFiles[0]];

/**
 * Delete operation with multiple files
 */
export const DeleteMultiple: Story = {
  args: {
    files: sampleFiles,
    operation: 'delete',
  },
};

/**
 * Delete operation with single file
 */
export const DeleteSingle: Story = {
  args: {
    files: singleFile,
    operation: 'delete',
  },
};

/**
 * Move operation
 */
export const MoveOperation: Story = {
  args: {
    files: sampleFiles,
    operation: 'move',
  },
};

/**
 * Rename operation
 */
export const RenameOperation: Story = {
  args: {
    files: sampleFiles,
    operation: 'rename',
  },
};

/**
 * Move operation with path entered
 */
export const MoveWithPath: Story = {
  args: {
    files: sampleFiles,
    operation: 'move',
  },
  decorators: [
    (Story) => (
      <div className="fixed inset-0 flex items-center justify-center">
        <Story />
      </div>
    ),
  ],
};

/**
 * Rename operation with prefix entered
 */
export const RenameWithPrefix: Story = {
  args: {
    files: sampleFiles,
    operation: 'rename',
  },
  decorators: [
    (Story) => (
      <div className="fixed inset-0 flex items-center justify-center">
        <Story />
      </div>
    ),
  ],
};

/**
 * Large batch (many files)
 */
export const LargeBatch: Story = {
  args: {
    files: [
      ...sampleFiles,
      {
        id: '4',
        name: 'File 4.mkv',
        path: '/movies/file4.mkv',
        type: 'file',
        size: 5 * 1024 * 1024 * 1024,
        mimeType: 'video/x-matroska',
        createdAt: '2024-01-01T10:00:00Z',
        updatedAt: '2024-01-15T10:00:00Z',
      },
      {
        id: '5',
        name: 'File 5.mkv',
        path: '/movies/file5.mkv',
        type: 'file',
        size: 6 * 1024 * 1024 * 1024,
        mimeType: 'video/x-matroska',
        createdAt: '2024-01-01T10:00:00Z',
        updatedAt: '2024-01-15T10:00:00Z',
      },
      {
        id: '6',
        name: 'File 6.mkv',
        path: '/movies/file6.mkv',
        type: 'file',
        size: 7 * 1024 * 1024 * 1024,
        mimeType: 'video/x-matroska',
        createdAt: '2024-01-01T10:00:00Z',
        updatedAt: '2024-01-15T10:00:00Z',
      },
    ],
    operation: 'delete',
  },
};
