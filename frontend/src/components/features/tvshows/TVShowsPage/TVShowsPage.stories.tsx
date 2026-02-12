import type { Meta, StoryObj } from '@storybook/react'
import TVShowsPage from './TVShowsPage'

const meta: Meta<typeof TVShowsPage> = {
  title: 'Features/TVShows/TVShowsPage',
  component: TVShowsPage,
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
type Story = StoryObj<typeof TVShowsPage>

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
