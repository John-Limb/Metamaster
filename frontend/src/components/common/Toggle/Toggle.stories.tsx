import type { Meta, StoryObj } from '@storybook/react'
import { Toggle } from './Toggle'

const meta: Meta<typeof Toggle> = {
  title: 'Components/Toggle',
  component: Toggle,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    disabled: {
      control: 'boolean',
    },
    size: {
      control: 'select',
      options: ['sm', 'md'],
    },
  },
}

export default meta
type Story = StoryObj<typeof Toggle>

export const Off: Story = {
  args: {
    label: 'Enable feature',
  },
}

export const On: Story = {
  args: {
    label: 'Enable feature',
    checked: true,
  },
}

export const Small: Story = {
  args: {
    label: 'Small toggle',
    size: 'sm',
  },
}

export const Medium: Story = {
  args: {
    label: 'Medium toggle',
    size: 'md',
  },
}

export const Disabled: Story = {
  args: {
    label: 'Disabled toggle',
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
    <div className="space-y-4">
      <Toggle label="WiFi" />
      <Toggle label="Bluetooth" checked />
      <Toggle label="Airplane Mode" />
    </div>
  ),
}

export const DarkMode: Story = {
  args: {
    label: 'Dark mode toggle',
  },
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
