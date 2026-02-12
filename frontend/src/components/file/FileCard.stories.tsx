import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { FileCard } from './FileCard';
import type { FileItem } from '@/types';

const meta = {
  title: 'File/FileCard',
  component: FileCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    isSelected: { control: 'boolean' },
    viewMode: { control: 'select', options: ['grid', 'list'] },
  },
  args: {
    onSelect: fn(),
    onDoubleClick: fn(),
    onContextMenu: fn(),
  },
} satisfies Meta<typeof FileCard>;

export default meta;
type Story = StoryObj<typeof meta>;

const sampleFile: FileItem = {
  id: '1',
  name: 'The Matrix (1999).mkv',
  path: '/movies/sci-fi/the-matrix-1999.mkv',
  type: 'file',
  size: 7.5 * 1024 * 1024 * 1024,
  mimeType: 'video/x-matroska',
  createdAt: '2024-01-01T10:00:00Z',
  updatedAt: '2024-01-15T10:00:00Z',
  isIndexed: true,
};

const sampleDirectory: FileItem = {
  id: '2',
  name: 'Sci-Fi Movies',
  path: '/movies/sci-fi',
  type: 'directory',
  size: 0,
  createdAt: '2024-01-01T10:00:00Z',
  updatedAt: '2024-01-15T10:00:00Z',
  isIndexed: true,
};

/**
 * Video file in grid view
 */
export const VideoFileGrid: Story = {
  args: {
    file: sampleFile,
    viewMode: 'grid',
  },
};

/**
 * Video file in list view
 */
export const VideoFileList: Story = {
  args: {
    file: sampleFile,
    viewMode: 'list',
  },
};

/**
 * Directory folder
 */
export const DirectoryGrid: Story = {
  args: {
    file: sampleDirectory,
    viewMode: 'grid',
  },
};

/**
 * Directory in list view
 */
export const DirectoryList: Story = {
  args: {
    file: sampleDirectory,
    viewMode: 'list',
  },
};

/**
 * Selected file
 */
export const Selected: Story = {
  args: {
    file: sampleFile,
    isSelected: true,
    viewMode: 'grid',
  },
};

/**
 * Selected in list view
 */
export const SelectedList: Story = {
  args: {
    file: sampleFile,
    isSelected: true,
    viewMode: 'list',
  },
};

/**
 * Image file
 */
export const ImageFile: Story = {
  args: {
    file: {
      ...sampleFile,
      id: '3',
      name: 'poster.jpg',
      mimeType: 'image/jpeg',
      size: 2 * 1024 * 1024,
    },
    viewMode: 'grid',
  },
};

/**
 * Audio file
 */
export const AudioFile: Story = {
  args: {
    file: {
      ...sampleFile,
      id: '4',
      name: 'soundtrack.mp3',
      mimeType: 'audio/mpeg',
      size: 10 * 1024 * 1024,
    },
    viewMode: 'grid',
  },
};

/**
 * Archive file
 */
export const ArchiveFile: Story = {
  args: {
    file: {
      ...sampleFile,
      id: '5',
      name: 'backup.zip',
      mimeType: 'application/zip',
      size: 5 * 1024 * 1024 * 1024,
    },
    viewMode: 'grid',
  },
};

/**
 * Unknown file type
 */
export const UnknownFile: Story = {
  args: {
    file: {
      ...sampleFile,
      id: '6',
      name: 'document.pdf',
      mimeType: 'application/pdf',
      size: 500 * 1024,
    },
    viewMode: 'grid',
  },
};

/**
 * Not indexed file
 */
export const NotIndexed: Story = {
  args: {
    file: {
      ...sampleFile,
      isIndexed: false,
    },
    viewMode: 'grid',
  },
};

/**
 * Large file
 */
export const LargeFile: Story = {
  args: {
    file: {
      ...sampleFile,
      id: '7',
      name: 'movie-4k.mkv',
      size: 80 * 1024 * 1024 * 1024,
    },
    viewMode: 'grid',
  },
};

/**
 * Small file
 */
export const SmallFile: Story = {
  args: {
    file: {
      ...sampleFile,
      id: '8',
      name: 'tiny-file.txt',
      size: 1024,
    },
    viewMode: 'grid',
  },
};
