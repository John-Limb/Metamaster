import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { useState } from 'react';
import { Toast, ToastContainer } from './Toast';
import type { Toast as ToastType } from '@/types';

const meta: Meta<typeof Toast> = {
  title: 'Common/Toast',
  component: Toast,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    type: { control: 'select', options: ['success', 'error', 'warning', 'info'] },
    message: { control: 'text' },
    duration: { control: 'number' },
  },
  args: {
    type: 'success',
    message: 'Operation completed successfully!',
    duration: 3000,
    onClose: fn(),
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

const ToastStoryWrapper = (args: any) => {
  const [isVisible, setIsVisible] = useState(true);
  return (
    <div>
      <button
        className="px-4 py-2 bg-gray-200 rounded mb-4"
        onClick={() => setIsVisible(!isVisible)}
      >
        {isVisible ? 'Hide' : 'Show'} Toast
      </button>
      {isVisible && <Toast id="story-toast" {...args} onClose={args.onClose} />}
    </div>
  );
};

/**
 * Success toast
 */
export const Success: Story = {
  args: {
    type: 'success',
    message: 'File uploaded successfully!',
  },
  render: (args) => <ToastStoryWrapper {...args} />,
};

/**
 * Error toast
 */
export const Error: Story = {
  args: {
    type: 'error',
    message: 'Failed to save file. Please try again.',
  },
  render: (args) => <ToastStoryWrapper {...args} />,
};

/**
 * Warning toast
 */
export const Warning: Story = {
  args: {
    type: 'warning',
    message: 'Low disk space. Consider cleaning up old files.',
  },
  render: (args) => <ToastStoryWrapper {...args} />,
};

/**
 * Info toast
 */
export const Info: Story = {
  args: {
    type: 'info',
    message: 'New update available. Restart to apply.',
  },
  render: (args) => <ToastStoryWrapper {...args} />,
};

/**
 * Toast with long duration
 */
export const LongDuration: Story = {
  args: {
    type: 'info',
    message: 'This toast will stay visible for 10 seconds.',
    duration: 10000,
  },
  render: (args) => <ToastStoryWrapper {...args} />,
};

/**
 * Toast with no auto-dismiss
 */
export const NoAutoDismiss: Story = {
  args: {
    type: 'info',
    message: 'This toast requires manual dismissal.',
    duration: 0,
  },
  render: (args) => <ToastStoryWrapper {...args} />,
};

// Toast Container Stories - separate meta for Storybook
const ToastContainerMeta: Meta<typeof ToastContainer> = {
  title: 'Common/Toast/ToastContainer',
  component: ToastContainer,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

// ToastContainerMeta is used for Storybook but not exported as default

const sampleToasts: ToastType[] = [
  { id: '1', type: 'success', message: 'File uploaded successfully!', duration: 5000 },
  { id: '2', type: 'info', message: 'Scan in progress...', duration: 0 },
  { id: '3', type: 'warning', message: 'Low storage space', duration: 8000 },
];

const ToastContainerStory = (args: any) => {
  const [toasts, setToasts] = useState<ToastType[]>(sampleToasts);
  const removeToast = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));
  return <ToastContainer toasts={toasts} onRemoveToast={removeToast} {...args} />;
};

type ToastContainerStoryObj = StoryObj<typeof ToastContainerMeta>;

/**
 * Multiple toasts in container
 */
export const MultipleToasts: ToastContainerStoryObj = {
  render: () => <ToastContainerStory />,
};

/**
 * Single toast
 */
export const SingleToast: ToastContainerStoryObj = {
  render: () => {
    const [toasts, setToasts] = useState<ToastType[]>([
      { id: '1', type: 'success', message: 'Operation completed!', duration: 5000 },
    ]);
    const removeToast = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));
    return <ToastContainer toasts={toasts} onRemoveToast={removeToast} />;
  },
};

/**
 * Empty container
 */
export const EmptyContainer: ToastContainerStoryObj = {
  render: () => {
    const [toasts, setToasts] = useState<ToastType[]>([]);
    const removeToast = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));
    return (
      <div>
        <p className="mb-4 text-gray-500">No toasts visible - container is empty</p>
        <ToastContainer toasts={toasts} onRemoveToast={removeToast} />
      </div>
    );
  },
};
