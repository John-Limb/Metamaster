import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { useState } from 'react';
import { ErrorModal } from './ErrorModal';

const meta = {
  title: 'Common/ErrorModal',
  component: ErrorModal,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  argTypes: {
    isOpen: { control: 'boolean' },
    isRetrying: { control: 'boolean' },
    title: { control: 'text' },
    message: { control: 'text' },
    details: { control: 'text' },
  },
  args: {
    isOpen: true,
    title: 'Error',
    message: 'Something went wrong. Please try again.',
    onClose: fn(),
    onRetry: fn(),
    isRetrying: false,
  },
} satisfies Meta<typeof ErrorModal>;

export default meta;
type Story = StoryObj<typeof meta>;

const ErrorModalWrapper = (args: any) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <button
        className="px-4 py-2 bg-red-600 text-white rounded"
        onClick={() => setIsOpen(true)}
      >
        Show Error
      </button>
      <ErrorModal
        {...args}
        isOpen={isOpen || args.isOpen}
        onClose={() => {
          args.onClose();
          setIsOpen(false);
        }}
        onRetry={async () => {
          args.onRetry();
          // Simulate retry delay
          await new Promise((resolve) => setTimeout(resolve, 1500));
        }}
      />
    </div>
  );
};

/**
 * Default error modal
 */
export const Default: Story = {
  args: {
    title: 'Connection Error',
    message: 'Failed to connect to the server. Please check your internet connection.',
  },
  render: (args) => <ErrorModalWrapper {...args} />,
};

/**
 * With error details
 */
export const WithDetails: Story = {
  args: {
    title: 'API Error',
    message: 'Failed to fetch movie data.',
    details: `Error: 500 Internal Server Error
    at Request.extractError (/api/movies:123)
    at processTicksAndRejections (node:internal/process/task_queues:95)
    at async handleRequest (/server:456)`,
  },
  render: (args) => <ErrorModalWrapper {...args} />,
};

/**
 * Without retry button
 */
export const NoRetry: Story = {
  args: {
    title: 'Permission Denied',
    message: 'You do not have permission to access this resource.',
    onRetry: undefined,
  },
  render: (args) => <ErrorModalWrapper {...args} />,
};

/**
 * Loading retry state
 */
export const Retrying: Story = {
  args: {
    title: 'Retrying...',
    message: 'Attempting to reconnect...',
    isRetrying: true,
  },
  render: (args) => <ErrorModalWrapper {...args} />,
};

/**
 * Validation error
 */
export const ValidationError: Story = {
  args: {
    title: 'Validation Error',
    message: 'The provided data is invalid.',
    details: `Validation failed:
    - title: Required field
    - year: Must be a valid year (1900-2100)
    - genre: Must be one of: Action, Comedy, Drama`,
  },
  render: (args) => <ErrorModalWrapper {...args} />,
};

/**
 * Network error
 */
export const NetworkError: Story = {
  args: {
    title: 'Network Error',
    message: 'Unable to reach the server. Please check your connection.',
    details: `Request failed with status code 503
    Service Unavailable

    The server may be down for maintenance or overloaded.`,
  },
  render: (args) => <ErrorModalWrapper {...args} />,
};

/**
 * Closed state
 */
export const Closed: Story = {
  args: {
    isOpen: false,
    title: 'Error',
    message: 'This modal is closed.',
    onRetry: fn(),
  },
  render: (args) => <ErrorModalWrapper {...args} />,
};
