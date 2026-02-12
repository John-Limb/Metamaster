import type { Meta, StoryObj } from '@storybook/react';
import { LibraryStats } from './LibraryStats';

const meta = {
  title: 'Dashboard/LibraryStats',
  component: LibraryStats,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    className: { control: 'text' },
  },
} satisfies Meta<typeof LibraryStats>;

export default meta;
type Story = StoryObj<typeof meta>;

const defaultStats = {
  totalMovies: 456,
  totalTVShows: 89,
  totalEpisodes: 2341,
  totalFiles: 1247,
  totalSize: 1024 * 1024 * 1024 * 500,
  lastUpdated: '2024-01-15T10:00:00Z',
};

/**
 * Default library stats
 */
export const Default: Story = {
  args: {
    stats: defaultStats,
  },
};

/**
 * Empty library
 */
export const Empty: Story = {
  args: {
    stats: {
      totalMovies: 0,
      totalTVShows: 0,
      totalEpisodes: 0,
      totalFiles: 0,
      totalSize: 0,
      lastUpdated: new Date().toISOString(),
    },
  },
};

/**
 * Large library
 */
export const LargeLibrary: Story = {
  args: {
    stats: {
      totalMovies: 5420,
      totalTVShows: 1250,
      totalEpisodes: 45000,
      totalFiles: 25000,
      totalSize: 1024 * 1024 * 1024 * 5000,
      lastUpdated: '2024-01-15T10:00:00Z',
    },
  },
};

/**
 * Recently updated
 */
export const RecentlyUpdated: Story = {
  args: {
    stats: {
      ...defaultStats,
      lastUpdated: new Date().toISOString(),
    },
  },
};

/**
 * Never updated
 */
export const NeverUpdated: Story = {
  args: {
    stats: {
      ...defaultStats,
      lastUpdated: '2020-01-01T00:00:00Z',
    },
  },
};
