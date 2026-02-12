import type { Meta, StoryObj } from '@storybook/react'
import { Card } from './Card'

const meta: Meta<typeof Card> = {
  title: 'Components/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'elevated', 'outlined'],
    },
    padding: {
      control: 'select',
      options: ['none', 'sm', 'md', 'lg'],
    },
  },
}

export default meta
type Story = StoryObj<typeof Card>

export const Default: Story = {
  args: {
    variant: 'default',
    padding: 'md',
    children: (
      <div>
        <h3 className="text-lg font-semibold text-secondary-900 dark:text-white mb-2">
          Card Title
        </h3>
        <p className="text-secondary-600 dark:text-secondary-400">
          This is a card with default variant styling.
        </p>
      </div>
    ),
  },
}

export const Elevated: Story = {
  args: {
    variant: 'elevated',
    padding: 'md',
    children: (
      <div>
        <h3 className="text-lg font-semibold text-secondary-900 dark:text-white mb-2">
          Elevated Card
        </h3>
        <p className="text-secondary-600 dark:text-secondary-400">
          This card has a medium shadow for elevation.
        </p>
      </div>
    ),
  },
}

export const Outlined: Story = {
  args: {
    variant: 'outlined',
    padding: 'md',
    children: (
      <div>
        <h3 className="text-lg font-semibold text-secondary-900 dark:text-white mb-2">
          Outlined Card
        </h3>
        <p className="text-secondary-600 dark:text-secondary-400">
          This card has only a border, no background.
        </p>
      </div>
    ),
  },
}

export const WithSubComponents: Story = {
  render: () => (
    <Card variant="default" className="w-96">
      <Card.Header>
        <h3 className="text-lg font-semibold text-secondary-900 dark:text-white">
          Card with Sections
        </h3>
      </Card.Header>
      <Card.Content>
        <p className="text-secondary-600 dark:text-secondary-400">
          This card demonstrates the use of Header, Content, and Footer sub-components.
        </p>
      </Card.Content>
      <Card.Footer>
        <div className="flex justify-end gap-2">
          <button className="px-4 py-2 text-sm text-secondary-600 hover:text-secondary-800 dark:text-secondary-400 dark:hover:text-secondary-200">
            Cancel
          </button>
          <button className="px-4 py-2 text-sm bg-primary-600 text-white rounded-md hover:bg-primary-700">
            Confirm
          </button>
        </div>
      </Card.Footer>
    </Card>
  ),
}

export const Clickable: Story = {
  args: {
    variant: 'default',
    padding: 'md',
    onClick: () => alert('Card clicked!'),
    children: (
      <div>
        <h3 className="text-lg font-semibold text-secondary-900 dark:text-white mb-2">
          Clickable Card
        </h3>
        <p className="text-secondary-600 dark:text-secondary-400">
          Click this card to trigger an action.
        </p>
      </div>
    ),
  },
}

export const DarkMode: Story = {
  args: {
    variant: 'elevated',
    padding: 'md',
    children: (
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">Dark Mode Card</h3>
        <p className="text-secondary-400">
          This card looks great in dark mode.
        </p>
      </div>
    ),
  },
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
