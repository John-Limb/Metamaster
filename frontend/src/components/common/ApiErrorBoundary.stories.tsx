import type { Meta, StoryObj } from '@storybook/react';
import { ApiErrorBoundary } from './ApiErrorBoundary';

const meta = {
  title: 'Common/ApiErrorBoundary',
  component: ApiErrorBoundary,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof ApiErrorBoundary>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default state - component renders children without errors
 */
export const Default: Story = {
  args: {
    children: (
      <div className="p-8">
        <h2 className="text-xl font-bold mb-4">Normal Content</h2>
        <p>This content is wrapped in an ApiErrorBoundary.</p>
        <p>No errors will occur in normal use.</p>
      </div>
    ),
  },
};

/**
 * With custom fallback
 */
export const WithCustomFallback: Story = {
  args: {
    fallback: (error, retry) => (
      <div className="p-8 bg-red-50 rounded-lg">
        <h2 className="text-xl font-bold text-red-600 mb-2">Custom Error Page</h2>
        <p className="text-red-500 mb-4">{error.message}</p>
        <button
          onClick={retry}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Try Again
        </button>
      </div>
    ),
    children: (
      <div className="p-8">
        <p className="mb-4">This story shows a custom fallback UI when an error occurs.</p>
        <p className="text-gray-500 text-sm">To test, wrap content that may throw errors.</p>
      </div>
    ),
  },
};

/**
 * Loading state within error boundary
 */
export const LoadingState: Story = {
  args: {
    children: (
      <div className="p-8">
        <p>Content that was loading when wrapped...</p>
      </div>
    ),
  },
};
