import type { Meta, StoryObj } from '@storybook/react'
import { ProgressBar } from './ProgressBar'

const meta: Meta<typeof ProgressBar> = {
  title: 'Components/ProgressBar',
  component: ProgressBar,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
    variant: {
      control: 'select',
      options: ['default', 'success', 'warning', 'danger'],
    },
    showLabel: {
      control: 'boolean',
    },
  },
}

export default meta
type Story = StoryObj<typeof ProgressBar>

export const Default: Story = {
  args: {
    value: 45,
  },
}

export const Small: Story = {
  args: {
    value: 45,
    size: 'sm',
  },
}

export const Medium: Story = {
  args: {
    value: 45,
    size: 'md',
  },
}

export const Large: Story = {
  args: {
    value: 45,
    size: 'lg',
  },
}

export const WithLabel: Story = {
  args: {
    value: 45,
    showLabel: true,
  },
}

export const Success: Story = {
  args: {
    value: 75,
    variant: 'success',
    showLabel: true,
  },
}

export const Warning: Story = {
  args: {
    value: 60,
    variant: 'warning',
    showLabel: true,
  },
}

export const Danger: Story = {
  args: {
    value: 85,
    variant: 'danger',
    showLabel: true,
  },
}

export const Zero: Story = {
  args: {
    value: 0,
  },
}

export const Full: Story = {
  args: {
    value: 100,
    variant: 'success',
  },
}

export const AllSizes: Story = {
  render: () => (
    <div className="w-80 space-y-4">
      <ProgressBar value={25} size="sm" />
      <ProgressBar value={50} size="md" />
      <ProgressBar value={75} size="lg" />
    </div>
  ),
}

export const AllVariants: Story = {
  render: () => (
    <div className="w-80 space-y-4">
      <ProgressBar value={25} variant="default" />
      <ProgressBar value={50} variant="success" />
      <ProgressBar value={75} variant="warning" />
      <ProgressBar value={90} variant="danger" />
    </div>
  ),
}

export const DarkMode: Story = {
  args: {
    value: 45,
  },
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
