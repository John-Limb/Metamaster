import type { Meta, StoryObj } from '@storybook/react'
import { Skeleton, SkeletonText, SkeletonAvatar, SkeletonCard, SkeletonTable } from './Skeleton'

const meta: Meta<typeof Skeleton> = {
  title: 'Components/Skeleton',
  component: Skeleton,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['text', 'circular', 'rectangular'],
    },
    animation: {
      control: 'select',
      options: ['pulse', 'wave', 'none'],
    },
  },
}

export default meta
type Story = StoryObj<typeof Skeleton>

export const Text: Story = {
  args: {
    variant: 'text',
    width: '100%',
    height: '1em',
  },
}

export const Circular: Story = {
  args: {
    variant: 'circular',
    width: 48,
    height: 48,
  },
}

export const Rectangular: Story = {
  args: {
    variant: 'rectangular',
    width: 200,
    height: 100,
  },
}

export const CustomSize: Story = {
  args: {
    variant: 'rectangular',
    width: 150,
    height: 40,
    radius: 8,
  },
}

export const NoAnimation: Story = {
  args: {
    variant: 'text',
    width: '100%',
    animation: 'none',
  },
}

export const TextLines: Story = {
  render: () => (
    <div className="w-80 space-y-2">
      <SkeletonText lines={4} />
    </div>
  ),
}

export const Avatar: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <SkeletonAvatar size={48} />
      <SkeletonAvatar size={40} />
      <SkeletonAvatar size={32} />
    </div>
  ),
}

export const Card: Story = {
  render: () => (
    <div className="w-80">
      <SkeletonCard />
    </div>
  ),
}

export const Table: Story = {
  render: () => (
    <div className="w-96">
      <SkeletonTable rows={5} columns={4} />
    </div>
  ),
}

export const Article: Story = {
  render: () => (
    <div className="w-full max-w-2xl space-y-4 p-4">
      <div className="flex items-center gap-4">
        <SkeletonAvatar size={56} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="40%" height="20px" />
          <Skeleton variant="text" width="30%" height="16px" />
        </div>
      </div>
      <SkeletonText lines={6} />
      <div className="flex gap-2 pt-2">
        <Skeleton width={80} height={32} radius={6} />
        <Skeleton width={80} height={32} radius={6} />
      </div>
    </div>
  ),
}

export const DarkMode: Story = {
  args: {
    variant: 'text',
    width: '100%',
    height: '1em',
  },
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
