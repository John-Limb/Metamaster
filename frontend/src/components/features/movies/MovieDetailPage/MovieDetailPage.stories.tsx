import type { Meta, StoryObj } from '@storybook/react'
import MovieDetailPage from './MovieDetailPage'
import { MemoryRouter } from 'react-router-dom'

const meta: Meta<typeof MovieDetailPage> = {
  title: 'Features/Movies/MovieDetailPage',
  component: MovieDetailPage,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <MemoryRouter initialEntries={['/movies/1']}>
        <Story />
      </MemoryRouter>
    ),
  ],
}

export default meta
type Story = StoryObj<typeof MovieDetailPage>

export const Default: Story = {}

export const NotFound: Story = {
  decorators: [
    (Story) => (
      <MemoryRouter initialEntries={['/movies/999']}>
        <Story />
      </MemoryRouter>
    ),
  ],
}
