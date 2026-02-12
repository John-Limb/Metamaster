import type { Meta, StoryObj } from '@storybook/react'
import { Select } from './Select'

const meta: Meta<typeof Select> = {
  title: 'Components/Select',
  component: Select,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    disabled: {
      control: 'boolean',
    },
    required: {
      control: 'boolean',
    },
  },
}

export default meta
type Story = StoryObj<typeof Select>

const options = [
  { value: 'option1', label: 'Option 1' },
  { value: 'option2', label: 'Option 2' },
  { value: 'option3', label: 'Option 3' },
  { value: 'option4', label: 'Option 4' },
]

export const Default: Story = {
  args: {
    options,
    placeholder: 'Select an option...',
  },
}

export const WithLabel: Story = {
  args: {
    label: 'Choose an option',
    options,
    placeholder: 'Select...',
  },
}

export const Required: Story = {
  args: {
    label: 'Category',
    options,
    required: true,
  },
}

export const WithError: Story = {
  args: {
    label: 'Selection',
    options,
    error: 'Please select an option',
  },
}

export const Disabled: Story = {
  args: {
    label: 'Disabled Select',
    options,
    disabled: true,
    value: 'option2',
  },
}

export const WithDisabledOption: Story = {
  args: {
    label: 'With Disabled Option',
    options: [
      { value: 'option1', label: 'Option 1' },
      { value: 'option2', label: 'Option 2', disabled: true },
      { value: 'option3', label: 'Option 3' },
    ],
  },
}

export const DarkMode: Story = {
  args: {
    label: 'Dark Mode Select',
    options,
    placeholder: 'Select...',
  },
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
