import type { Meta, StoryObj } from '@storybook/react'
import { TVShowCard } from './TVShowCard'

const meta: Meta<typeof TVShowCard> = {
  title: 'Features/TVShows/TVShowCard',
  component: TVShowCard,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    rating: {
      control: { type: 'range', min: 0, max: 10, step: 0.1 },
    },
  },
}

export default meta
type Story = StoryObj<typeof TVShowCard>

export const Default: Story = {
  args: {
    id: '1',
    title: 'Breaking Bad',
    posterUrl: 'https://images.unsplash.com/photo-1517604931442-710c8ed6e31f?w=300&h=450&fit=crop',
    seasons: 5,
    episodes: 62,
    status: 'ended',
    rating: 9.5,
    genres: ['Crime', 'Drama'],
    onClick: () => console.log('Show clicked'),
    onAddToQueue: () => console.log('Add to queue'),
    onEdit: () => console.log('Edit'),
    onDelete: () => console.log('Delete'),
  },
}

export const Continuing: Story = {
  args: {
    id: '2',
    title: 'The Walking Dead',
    posterUrl: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=300&h=450&fit=crop',
    seasons: 11,
    episodes: 177,
    status: 'continuing',
    rating: 8.2,
    genres: ['Horror', 'Drama'],
    nextEpisode: {
      season: 11,
      episode: 24,
      airDate: 'Nov 20',
    },
    onClick: () => console.log('Show clicked'),
  },
}

export const WithNextEpisode: Story = {
  args: {
    id: '3',
    title: 'Stranger Things',
    posterUrl: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=300&h=450&fit=crop',
    seasons: 4,
    episodes: 42,
    status: 'returning',
    rating: 8.7,
    genres: ['Sci-Fi', 'Horror'],
    nextEpisode: {
      season: 5,
      episode: 1,
      airDate: 'TBA',
    },
    onClick: () => console.log('Show clicked'),
  },
}

export const WithoutPoster: Story = {
  args: {
    id: '4',
    title: 'Unknown Show',
    seasons: 2,
    episodes: 20,
    status: 'ended',
    onClick: () => console.log('Show clicked'),
  },
}

export const NoActions: Story = {
  args: {
    id: '5',
    title: 'Minimal Show',
    seasons: 1,
    episodes: 10,
    onClick: () => console.log('Show clicked'),
  },
}

export const LowRating: Story = {
  args: {
    id: '6',
    title: 'Not So Great Show',
    posterUrl: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=300&h=450&fit=crop',
    seasons: 3,
    episodes: 45,
    status: 'ended',
    rating: 5.2,
    genres: ['Comedy'],
    onClick: () => console.log('Show clicked'),
  },
}
