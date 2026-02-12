import type { Meta, StoryObj } from '@storybook/react';
import { Dashboard } from './Dashboard';

const meta = {
  title: 'Dashboard/Dashboard',
  component: Dashboard,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  argTypes: {
    className: { control: 'text' },
  },
} satisfies Meta<typeof Dashboard>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default dashboard view
 */
export const Default: Story = {};

/**
 * Dashboard with all data populated
 */
export const FullData: Story = {
  args: {
    className: 'max-w-7xl mx-auto',
  },
};

/**
 * Empty state (no data)
 */
export const Empty: Story = {
  args: {
    className: 'max-w-7xl mx-auto',
  },
  decorators: [
    (Story) => (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500 mt-1">Welcome back! Here's an overview of your library.</p>
          </div>
        </div>
        <Story />
      </div>
    ),
  ],
};

/**
 * Dashboard in dark mode context
 */
export const DarkMode: Story = {
  args: {
    className: 'max-w-7xl mx-auto',
  },
  decorators: [
    (Story) => (
      <div className="dark bg-gray-900 min-h-screen p-6">
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Dashboard</h1>
              <p className="text-gray-400 mt-1">Welcome back! Here's an overview of your library.</p>
            </div>
            <div className="flex items-center gap-2">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Refresh Data
              </button>
            </div>
          </div>
          <Story />
        </div>
      </div>
    ),
  ],
};
