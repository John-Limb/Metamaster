import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { ErrorBoundary } from './ErrorBoundary';

const meta = {
  title: 'Common/ErrorBoundary',
  component: ErrorBoundary,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  args: {},
} satisfies Meta<typeof ErrorBoundary>;

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
        <p>This content is wrapped in an ErrorBoundary.</p>
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
        <h2 className="text-xl font-bold text-red-600 mb-2">Custom Error Handler</h2>
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
      </div>
    ),
  },
};

/**
 * Minimal fallback
 */
export const MinimalFallback: Story = {
  args: {
    fallback: (error, retry) => (
      <div className="p-4 border border-red-300 rounded bg-red-50">
        <p className="text-red-600">Error: {error.message}</p>
        <button onClick={retry} className="mt-2 text-blue-600 underline">
          Retry
        </button>
      </div>
    ),
    children: (
      <div className="p-8">
        <p>Content with minimal error handling.</p>
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

/**
 * With multiple children
 */
export const MultipleChildren: Story = {
  args: {
    children: (
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Multiple Child Components</h2>
        <p>This error boundary wraps multiple components.</p>
        <div className="p-4 bg-gray-100 rounded">
          <p>Child component 1</p>
        </div>
        <div className="p-4 bg-gray-100 rounded">
          <p>Child component 2</p>
        </div>
      </div>
    ),
  },
};
