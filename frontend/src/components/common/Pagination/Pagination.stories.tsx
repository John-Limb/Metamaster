import type { Meta, StoryObj } from '@storybook/react'
import { Pagination } from './Pagination'

const meta: Meta<typeof Pagination> = {
  title: 'Components/Pagination',
  component: Pagination,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    showFirstLast: {
      control: 'boolean',
    },
  },
}

export default meta
type Story = StoryObj<typeof Pagination>

export const Default: Story = {
  args: {
    currentPage: 1,
    totalPages: 10,
    onPageChange: (page) => console.log('Page:', page),
  },
}

export const MiddlePage: Story = {
  args: {
    currentPage: 5,
    totalPages: 10,
    onPageChange: (page) => console.log('Page:', page),
  },
}

export const LastPage: Story = {
  args: {
    currentPage: 10,
    totalPages: 10,
    onPageChange: (page) => console.log('Page:', page),
  },
}

export const NoFirstLast: Story = {
  args: {
    currentPage: 3,
    totalPages: 10,
    showFirstLast: false,
    onPageChange: (page) => console.log('Page:', page),
  },
}

export const ManyPages: Story = {
  args: {
    currentPage: 50,
    totalPages: 100,
    onPageChange: (page) => console.log('Page:', page),
  },
}

export const FewPages: Story = {
  args: {
    currentPage: 1,
    totalPages: 3,
    onPageChange: (page) => console.log('Page:', page),
  },
}

export const SinglePage: Story = {
  args: {
    currentPage: 1,
    totalPages: 1,
    onPageChange: (page) => console.log('Page:', page),
  },
}

export const DarkMode: Story = {
  args: {
    currentPage: 3,
    totalPages: 10,
    onPageChange: (page) => console.log('Page:', page),
  },
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
