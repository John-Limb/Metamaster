import type { Meta, StoryObj } from '@storybook/react';
import { Breadcrumb } from './Breadcrumb';

const meta = {
  title: 'Common/Breadcrumb',
  component: Breadcrumb,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  argTypes: {
    showHome: { control: 'boolean' },
    separator: { control: 'text' },
    className: { control: 'text' },
  },
} satisfies Meta<typeof Breadcrumb>;

export default meta;
type Story = StoryObj<typeof meta>;

const items = [
  { label: 'Movies', path: '/movies' },
  { label: 'Action', path: '/movies/action' },
  { label: 'The Matrix', path: '/movies/action/the-matrix' },
];

/**
 * Default breadcrumb with navigation items
 */
export const Default: Story = {
  args: {
    items,
  },
};

/**
 * Breadcrumb with home link
 */
export const WithHome: Story = {
  args: {
    items,
    showHome: true,
    onHomeClick: () => alert('Home clicked'),
  },
};

/**
 * Custom separator
 */
export const CustomSeparator: Story = {
  args: {
    items,
    separator: '/',
  },
};

/**
 * Clickable items with custom actions
 */
export const WithClickActions: Story = {
  args: {
    items: [
      { label: 'Home', path: '/' },
      { label: 'Library', onClick: () => alert('Library clicked') },
      { label: 'Movies', path: '/movies' },
      { label: 'Current Folder' },
    ],
    showHome: true,
    onHomeClick: () => alert('Home clicked'),
  },
};

/**
 * Single item
 */
export const SingleItem: Story = {
  args: {
    items: [{ label: 'All Files', path: '/files' }],
  },
};

/**
 * Deeply nested path
 */
export const DeepNesting: Story = {
  args: {
    items: [
      { label: 'Home', path: '/' },
      { label: 'Media', path: '/media' },
      { label: 'Movies', path: '/media/movies' },
      { label: 'Action', path: '/media/movies/action' },
      { label: 'Sci-Fi', path: '/media/movies/action/sci-fi' },
      { label: 'The Matrix Collection', path: '/media/movies/action/sci-fi/matrix' },
    ],
    showHome: true,
    onHomeClick: () => alert('Home clicked'),
  },
};

/**
 * Current location (last item not clickable)
 */
export const CurrentLocation: Story = {
  args: {
    items: [
      { label: 'Movies', path: '/movies' },
      { label: 'Action', path: '/movies/action' },
      { label: 'The Matrix (1999)' },
    ],
  },
};
