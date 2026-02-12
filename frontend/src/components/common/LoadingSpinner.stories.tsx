import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { LoadingSpinner } from './LoadingSpinner';

const meta = {
  title: 'Common/LoadingSpinner',
  component: LoadingSpinner,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
    },
  },
} satisfies Meta<typeof LoadingSpinner>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Small: Story = {
  args: {
    size: 'sm',
    message: 'Loading...',
  },
};

export const Medium: Story = {
  args: {
    size: 'md',
    message: 'Loading data...',
  },
};

export const Large: Story = {
  args: {
    size: 'lg',
    message: 'Please wait while we process your request...',
  },
};

export const WithoutMessage: Story = {
  args: {
    size: 'lg',
  },
};

export const FullPage: Story = {
  args: {
    size: 'lg',
    fullScreen: true,
    message: 'Loading application...',
  },
};

export const Overlay: Story = {
  args: {
    size: 'lg',
    overlay: true,
    message: 'Saving changes...',
  },
};
