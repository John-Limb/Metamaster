import type { Meta, StoryObj } from '@storybook/react'
import { FilterPanel } from './FilterPanel'

const meta: Meta<typeof FilterPanel> = {
  title: 'Features/FilterPanel',
  component: FilterPanel,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    isOpen: {
      control: 'boolean',
    },
  },
}

export default meta
type Story = StoryObj<typeof FilterPanel>

const mockSections = [
  {
    id: 'genre',
    label: 'Genre',
    options: [
      { value: 'action', label: 'Action', count: 24 },
      { value: 'comedy', label: 'Comedy', count: 18 },
      { value: 'drama', label: 'Drama', count: 32 },
      { value: 'horror', label: 'Horror', count: 12 },
      { value: 'sci-fi', label: 'Sci-Fi', count: 15 },
      { value: 'thriller', label: 'Thriller', count: 21 },
    ],
    multiSelect: true,
  },
  {
    id: 'year',
    label: 'Year',
    options: [
      { value: '2024', label: '2024', count: 5 },
      { value: '2023', label: '2023', count: 12 },
      { value: '2022', label: '2022', count: 18 },
      { value: '2021', label: '2021', count: 15 },
      { value: '2020', label: '2020', count: 22 },
    ],
    multiSelect: true,
  },
  {
    id: 'rating',
    label: 'Rating',
    options: [
      { value: '5', label: '5 Stars', count: 8 },
      { value: '4', label: '4+ Stars', count: 25 },
      { value: '3', label: '3+ Stars', count: 45 },
      { value: '2', label: '2+ Stars', count: 62 },
    ],
    multiSelect: false,
  },
]

export const Default: Story = {
  args: {
    sections: mockSections,
    selectedFilters: {},
    onFilterChange: (sectionId, values) => console.log('Filter change:', sectionId, values),
    onClearAll: () => console.log('Clear all'),
    isOpen: true,
    onToggle: () => console.log('Toggle'),
  },
}

export const WithActiveFilters: Story = {
  args: {
    sections: mockSections,
    selectedFilters: {
      genre: ['action', 'horror'],
      year: ['2023', '2022'],
    },
    onFilterChange: (sectionId, values) => console.log('Filter change:', sectionId, values),
    onClearAll: () => console.log('Clear all'),
    isOpen: true,
    onToggle: () => console.log('Toggle'),
  },
}

export const Closed: Story = {
  args: {
    sections: mockSections,
    selectedFilters: {},
    onFilterChange: (sectionId, values) => console.log('Filter change:', sectionId, values),
    onClearAll: () => console.log('Clear all'),
    isOpen: false,
    onToggle: () => console.log('Toggle'),
  },
}

export const SingleSelectFilters: Story = {
  args: {
    sections: mockSections.filter((s) => s.id === 'rating'),
    selectedFilters: { rating: ['4'] },
    onFilterChange: (sectionId, values) => console.log('Filter change:', sectionId, values),
    onClearAll: () => console.log('Clear all'),
    isOpen: true,
    onToggle: () => console.log('Toggle'),
  },
}
