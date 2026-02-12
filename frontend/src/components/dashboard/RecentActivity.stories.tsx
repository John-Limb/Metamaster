import type { Meta, StoryObj } from '@storybook/react';
import { RecentActivity } from './RecentActivity';

const meta = {
  title: 'Dashboard/RecentActivity',
  component: RecentActivity,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    className: { control: 'text' },
  },
} satisfies Meta<typeof RecentActivity>;

export default meta;
type Story = StoryObj<typeof meta>;

const defaultActivities = [
  {
    id: '1',
    type: 'scan' as const,
    title: 'Library Scan Complete',
    description: 'Scanned 45 new files',
    timestamp: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    type: 'sync' as const,
    title: 'Metadata Sync',
    description: 'Updated metadata for 12 movies',
    timestamp: '2024-01-15T08:00:00Z',
  },
  {
    id: '3',
    type: 'add' as const,
    title: 'New Content Added',
    description: 'Added "The Matrix" to library',
    timestamp: '2024-01-15T05:00:00Z',
  },
  {
    id: '4',
    type: 'delete' as const,
    title: 'File Removed',
    description: 'Removed "Old Movie.mkv"',
    timestamp: '2024-01-14T15:00:00Z',
  },
  {
    id: '5',
    type: 'update' as const,
    title: 'Metadata Updated',
    description: 'Updated info for "Inception.mkv"',
    timestamp: '2024-01-14T12:00:00Z',
  },
];

/**
 * Default recent activity with multiple entries
 */
export const Default: Story = {
  args: {
    activities: defaultActivities,
  },
};

/**
 * Single activity
 */
export const SingleActivity: Story = {
  args: {
    activities: [defaultActivities[0]],
  },
};

/**
 * Empty state
 */
export const Empty: Story = {
  args: {
    activities: [],
  },
};

/**
 * All activity types
 */
export const AllTypes: Story = {
  args: {
    activities: [
      {
        id: 'scan',
        type: 'scan' as const,
        title: 'Library Scan',
        description: 'Scanned library for new content',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'sync',
        type: 'sync' as const,
        title: 'Metadata Sync',
        description: 'Synchronized with online database',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'add',
        type: 'add' as const,
        title: 'File Added',
        description: 'Added new file to library',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'delete',
        type: 'delete' as const,
        title: 'File Deleted',
        description: 'Removed file from library',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'update',
        type: 'update' as const,
        title: 'Metadata Updated',
        description: 'Updated file information',
        timestamp: new Date().toISOString(),
      },
    ],
  },
};

/**
 * Long history
 */
export const LongHistory: Story = {
  args: {
    activities: [
      ...defaultActivities,
      {
        id: '6',
        type: 'scan' as const,
        title: 'Quick Scan',
        description: 'Completed quick scan',
        timestamp: '2024-01-13T10:00:00Z',
      },
      {
        id: '7',
        type: 'add' as const,
        title: 'Batch Import',
        description: 'Imported 10 files',
        timestamp: '2024-01-12T14:00:00Z',
      },
    ],
  },
};
