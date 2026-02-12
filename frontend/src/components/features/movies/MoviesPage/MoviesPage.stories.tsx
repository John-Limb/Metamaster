import type { Meta, StoryObj } from '@storybook/react'
import MoviesPage from './MoviesPage'

const meta: Meta<typeof MoviesPage> = {
  title: 'Features/Movies/MoviesPage',
  component: MoviesPage,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div className="dark">
        <Story />
      </div>
    ),
  ],
}

export default meta
type Story = StoryObj<typeof MoviesPage>

export const Default: Story = {}

export const Loading: Story = {
  decorators: [
    (Story) => (
      <div className="dark">
        <Story />
      </div>
    ),
  ],
}
