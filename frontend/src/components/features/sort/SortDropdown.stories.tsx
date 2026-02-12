import type { Meta, StoryObj } from '@storybook/react'
import { SortDropdown } from './SortDropdown'

const meta: Meta<typeof SortDropdown> = {
  title: 'Features/SortDropdown',
  component: SortDropdown,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: 'select',
      options: ['title-asc', 'title-desc', 'year-asc', 'year-desc', 'rating-asc', 'rating-desc'],
    },
  },
}

export default meta
type Story = StoryObj<typeof SortDropdown>

const sortOptions = [
  { value: 'title-asc', label: 'Title', direction: 'asc' },
  { value: 'title-desc', label: 'Title', direction: 'desc' },
  { value: 'year-asc', label: 'Year', direction: 'asc' },
  { value: 'year-desc', label: 'Year', direction: 'desc' },
  { value: 'rating-asc', label: 'Rating', direction: 'asc' },
  { value: 'rating-desc', label: 'Rating', direction: 'desc' },
  { value: 'date-added', label: 'Date Added' },
]

export const Default: Story = {
  args: {
    options: sortOptions,
    value: 'title-asc',
    onChange: (value) => console.log('Sort change:', value),
  },
}

export const SortedByYear: Story = {
  args: {
    options: sortOptions,
    value: 'year-desc',
    onChange: (value) => console.log('Sort change:', value),
  },
}

export const SortedByRating: Story = {
  args: {
    options: sortOptions,
    value: 'rating-desc',
    onChange: (value) => console.log('Sort change:', value),
  },
}

export const SortedByDate: Story = {
  args: {
    options: sortOptions,
    value: 'date-added',
    onChange: (value) => console.log('Sort change:', value),
  },
}

export const TVShowSortOptions: Story = {
  args: {
    options: [
      { value: 'name-asc', label: 'Name', direction: 'asc' },
      { value: 'name-desc', label: 'Name', direction: 'desc' },
      { value: 'premiere-asc', label: 'Premiere Date', direction: 'asc' },
      { value: 'premiere-desc', label: 'Premiere Date', direction: 'desc' },
      { value: 'rating-asc', label: 'Rating', direction: 'asc' },
      { value: 'rating-desc', label: 'Rating', direction: 'desc' },
      { value: 'episodes', label: 'Episode Count' },
    ],
    value: 'name-asc',
    onChange: (value) => console.log('Sort change:', value),
  },
}
