import type { Meta, StoryObj } from '@storybook/react';
import { NotFound } from './NotFound';

const meta = {
  title: 'Common/NotFound',
  component: NotFound,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  argTypes: {
    title: { control: 'text' },
    message: { control: 'text' },
    showBackButton: { control: 'boolean' },
  },
  args: {
    title: 'Page Not Found',
    message: 'The page you are looking for does not exist.',
    showBackButton: true,
  },
} satisfies Meta<typeof NotFound>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default 404 page
 */
export const Default: Story = {};

/**
 * Custom title and message
 */
export const CustomMessage: Story = {
  args: {
    title: 'Movie Not Found',
    message: 'The movie you are looking for has been removed or never existed.',
  },
};

/**
 * Without back button
 */
export const NoBackButton: Story = {
  args: {
    showBackButton: false,
  },
};

/**
 * Search result not found
 */
export const SearchNotFound: Story = {
  args: {
    title: 'No Results Found',
    message: 'We could not find any movies matching your search criteria. Try adjusting your filters.',
  },
};

/**
 * File not found
 */
export const FileNotFound: Story = {
  args: {
    title: 'File Not Found',
    message: 'The file you are trying to access has been moved, renamed, or deleted.',
  },
};

/**
 * Empty state variant (not technically 404)
 */
export const EmptyState: Story = {
  args: {
    title: 'No Content Yet',
    message: 'Add some files to your library to get started.',
    showBackButton: false,
  },
};

/**
 * Library empty state
 */
export const EmptyLibrary: Story = {
  args: {
    title: 'Your Library is Empty',
    message: 'Start by adding your movie or TV show collection. Supported formats include MP4, MKV, and more.',
    showBackButton: false,
  },
};
