import type { Meta, StoryObj } from '@storybook/react'
import TVShowDetailPage from './TVShowDetailPage'
import { MemoryRouter } from 'react-router-dom'

const meta: Meta<typeof TVShowDetailPage> = {
  title: 'Features/TVShows/TVShowDetailPage',
  component: TVShowDetailPage,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <MemoryRouter initialEntries={['/tv-shows/1']}>
        <Story />
      </MemoryRouter>
    ),
  ],
}

export default meta
type Story = StoryObj<typeof TVShowDetailPage>

export const Default: Story = {}

export const NotFound: Story = {
  decorators: [
    (Story) => (
      <MemoryRouter initialEntries={['/tv-shows/999']}>
        <Story />
      </MemoryRouter>
    ),
  ],
}
