import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { useState } from 'react';
import { ConfirmDialog } from './ConfirmDialog';

const meta = {
  title: 'Common/ConfirmDialog',
  component: ConfirmDialog,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  argTypes: {
    isOpen: { control: 'boolean' },
    isDangerous: { control: 'boolean' },
    isLoading: { control: 'boolean' },
    confirmText: { control: 'text' },
    cancelText: { control: 'text' },
  },
  args: {
    isOpen: true,
    title: 'Confirm Action',
    message: 'Are you sure you want to proceed with this action?',
    confirmText: 'Confirm',
    cancelText: 'Cancel',
    isDangerous: false,
    isLoading: false,
    onConfirm: fn(),
    onCancel: fn(),
  },
} satisfies Meta<typeof ConfirmDialog>;

export default meta;
type Story = StoryObj<typeof meta>;

const ConfirmDialogWrapper = (args: any) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div>
      <button
        className="px-4 py-2 bg-blue-600 text-white rounded"
        onClick={() => setIsOpen(true)}
      >
        Open Dialog
      </button>
      <ConfirmDialog
        {...args}
        isOpen={isOpen || args.isOpen}
        onCancel={() => {
          args.onCancel();
          setIsOpen(false);
        }}
        onConfirm={() => {
          args.onConfirm();
          setIsOpen(false);
        }}
      />
    </div>
  );
};

/**
 * Default confirmation dialog
 */
export const Default: Story = {
  args: {
    title: 'Delete File',
    message: 'Are you sure you want to delete this file? This action cannot be undone.',
  },
  render: (args) => <ConfirmDialogWrapper {...args} />,
};

/**
 * Dangerous action (red confirm button)
 */
export const DangerousAction: Story = {
  args: {
    title: 'Delete Permanently',
    message: 'This will permanently delete all selected files. This action cannot be undone.',
    confirmText: 'Delete',
    isDangerous: true,
  },
  render: (args) => <ConfirmDialogWrapper {...args} />,
};

/**
 * Loading state
 */
export const Loading: Story = {
  args: {
    title: 'Processing',
    message: 'Please wait while we process your request...',
    isLoading: true,
    confirmText: 'Processing...',
  },
  render: (args) => <ConfirmDialogWrapper {...args} />,
};

/**
 * Custom button text
 */
export const CustomButtons: Story = {
  args: {
    title: 'Save Changes',
    message: 'Do you want to save your changes before leaving?',
    confirmText: 'Save',
    cancelText: 'Discard',
  },
  render: (args) => <ConfirmDialogWrapper {...args} />,
};

/**
 * Information dialog (non-destructive)
 */
export const Information: Story = {
  args: {
    title: 'Information',
    message: 'This is an informational message for the user.',
    confirmText: 'OK',
    cancelText: undefined,
  },
  render: (args) => <ConfirmDialogWrapper {...args} />,
};

/**
 * Closed state
 */
export const Closed: Story = {
  args: {
    isOpen: false,
    title: 'Dialog',
    message: 'This dialog is closed.',
  },
  render: (args) => <ConfirmDialogWrapper {...args} />,
};
