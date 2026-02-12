import type { Meta, StoryObj } from '@storybook/react';
import { StorageChart } from './StorageChart';

const meta = {
  title: 'Dashboard/StorageChart',
  component: StorageChart,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    className: { control: 'text' },
  },
} satisfies Meta<typeof StorageChart>;

export default meta;
type Story = StoryObj<typeof meta>;

const defaultData = [
  { label: 'Movies', value: 250 * 1024 * 1024 * 1024, color: '#3b82f6' },
  { label: 'TV Shows', value: 180 * 1024 * 1024 * 1024, color: '#8b5cf6' },
  { label: 'Music', value: 50 * 1024 * 1024 * 1024, color: '#10b981' },
  { label: 'Other', value: 20 * 1024 * 1024 * 1024, color: '#f59e0b' },
];

const defaultTotal = defaultData.reduce((acc, item) => acc + item.value, 0);

/**
 * Default storage chart with all data
 */
export const Default: Story = {
  args: {
    data: defaultData,
    total: defaultTotal,
  },
};

/**
 * Single category
 */
export const SingleCategory: Story = {
  args: {
    data: [{ label: 'Movies', value: 500 * 1024 * 1024 * 1024, color: '#3b82f6' }],
    total: 500 * 1024 * 1024 * 1024,
  },
};

/**
 * Empty storage
 */
export const Empty: Story = {
  args: {
    data: [],
    total: 0,
  },
};

/**
 * Full storage
 */
export const FullStorage: Story = {
  args: {
    data: [
      { label: 'Movies', value: 800 * 1024 * 1024 * 1024, color: '#3b82f6' },
      { label: 'TV Shows', value: 600 * 1024 * 1024 * 1024, color: '#8b5cf6' },
      { label: 'Music', value: 200 * 1024 * 1024 * 1024, color: '#10b981' },
      { label: 'Other', value: 100 * 1024 * 1024 * 1024, color: '#f59e0b' },
    ],
    total: 1700 * 1024 * 1024 * 1024,
  },
};

/**
 * Small library
 */
export const SmallLibrary: Story = {
  args: {
    data: [
      { label: 'Movies', value: 10 * 1024 * 1024 * 1024, color: '#3b82f6' },
      { label: 'TV Shows', value: 5 * 1024 * 1024 * 1024, color: '#8b5cf6' },
    ],
    total: 15 * 1024 * 1024 * 1024,
  },
};

/**
 * Many categories
 */
export const ManyCategories: Story = {
  args: {
    data: [
      { label: 'Movies', value: 200, color: '#3b82f6' },
      { label: 'TV Shows', value: 150, color: '#8b5cf6' },
      { label: 'Music', value: 50, color: '#10b981' },
      { label: 'Documents', value: 30, color: '#f59e0b' },
      { label: 'Images', value: 20, color: '#ef4444' },
      { label: 'Archives', value: 10, color: '#6366f1' },
    ],
    total: 460,
  },
};
