import type { Meta, StoryObj } from '@storybook/react'
import { Checkbox } from './Checkbox'

const meta: Meta<typeof Checkbox> = {
  title: 'Components/Checkbox',
  component: Checkbox,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    disabled: {
      control: 'boolean',
    },
  },
}

export default meta
type Story = StoryObj<typeof Checkbox>

export const Unchecked: Story = {
  args: {
    label: 'I agree to the terms and conditions',
  },
}

export const Checked: Story = {
  args: {
    label: 'I agree to the terms and conditions',
    checked: true,
  },
}

export const WithError: Story = {
  args: {
    label: 'I agree to the terms and conditions',
    error: 'You must agree to the terms',
  },
}

export const Disabled: Story = {
  args: {
    label: 'Disabled checkbox',
    disabled: true,
  },
}

export const CheckedDisabled: Story = {
  args: {
    label: 'Checked and disabled',
    checked: true,
    disabled: true,
  },
}

export const Group: Story = {
  render: () => (
    <div className="space-y-2">
      <Checkbox label="Option 1" />
      <Checkbox label="Option 2" />
      <Checkbox label="Option 3" />
    </div>
  ),
}

export const DarkMode: Story = {
  args: {
    label: 'Dark mode checkbox',
  },
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
