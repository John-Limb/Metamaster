import type { Meta, StoryObj } from '@storybook/react'
import { MovieCard } from './MovieCard'

const meta: Meta<typeof MovieCard> = {
  title: 'Features/Movies/MovieCard',
  component: MovieCard,
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
type Story = StoryObj<typeof MovieCard>

export const Default: Story = {
  args: {
    id: '1',
    title: 'Inception',
    posterUrl: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=300&h=450&fit=crop',
    year: 2010,
    rating: 8.8,
    genres: ['Action', 'Sci-Fi'],
    quality: '4K',
    onClick: () => console.log('Movie clicked'),
    onAddToQueue: () => console.log('Add to queue'),
    onEdit: () => console.log('Edit'),
    onDelete: () => console.log('Delete'),
  },
}

export const WithHighRating: Story = {
  args: {
    id: '2',
    title: 'The Shawshank Redemption',
    posterUrl: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=300&h=450&fit=crop',
    year: 1994,
    rating: 9.3,
    genres: ['Drama'],
    quality: '1080p',
    onClick: () => console.log('Movie clicked'),
  },
}

export const WithoutPoster: Story = {
  args: {
    id: '3',
    title: 'Unknown Movie',
    year: 2023,
    rating: 7.5,
    genres: ['Thriller'],
    onClick: () => console.log('Movie clicked'),
  },
}

export const WithMultipleGenres: Story = {
  args: {
    id: '4',
    title: 'Interstellar',
    posterUrl: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=300&h=450&fit=crop',
    year: 2014,
    rating: 8.6,
    genres: ['Adventure', 'Drama', 'Sci-Fi'],
    quality: '4K',
    onClick: () => console.log('Movie clicked'),
  },
}

export const NoActions: Story = {
  args: {
    id: '5',
    title: 'Minimal Movie',
    year: 2022,
    genres: ['Comedy'],
    onClick: () => console.log('Movie clicked'),
  },
}

export const LowRating: Story = {
  args: {
    id: '6',
    title: 'Not So Great Movie',
    posterUrl: 'https://images.unsplash.com/photo-1517604931442-710c8ed6e31f?w=300&h=450&fit=crop',
    year: 2021,
    rating: 4.2,
    genres: ['Horror'],
    onClick: () => console.log('Movie clicked'),
  },
}
