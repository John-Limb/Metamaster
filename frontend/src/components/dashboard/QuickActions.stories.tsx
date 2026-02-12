import type { Meta, StoryObj } from '@storybook/react';
import { QuickActions } from './QuickActions';

const meta = {
  title: 'Dashboard/QuickActions',
  component: QuickActions,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    className: { control: 'text' },
  },
} satisfies Meta<typeof QuickActions>;

export default meta;
type Story = StoryObj<typeof meta>;

const defaultActions = [
  {
    id: 'scan',
    label: 'Scan Library',
    description: 'Scan for new files',
    variant: 'primary' as const,
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    onClick: () => alert('Scan clicked'),
  },
  {
    id: 'sync',
    label: 'Sync Metadata',
    description: 'Update all metadata',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.001 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    onClick: () => alert('Sync clicked'),
  },
  {
    id: 'add',
    label: 'Add Files',
    description: 'Add new content',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
      </svg>
    ),
    onClick: () => alert('Add clicked'),
  },
  {
    id: 'settings',
    label: 'Settings',
    description: 'Configure options',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    onClick: () => alert('Settings clicked'),
  },
];

/**
 * Default quick actions with all actions
 */
export const Default: Story = {
  args: {
    actions: defaultActions,
  },
};

/**
 * Single action
 */
export const SingleAction: Story = {
  args: {
    actions: [defaultActions[0]],
  },
};

/**
 * Two actions
 */
export const TwoActions: Story = {
  args: {
    actions: defaultActions.slice(0, 2),
  },
};

/**
 * Custom styled actions
 */
export const CustomStyled: Story = {
  args: {
    actions: [
      {
        id: 'custom',
        label: 'Custom Action',
        description: 'A custom styled action',
        variant: 'primary' as const,
        icon: (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        ),
        onClick: () => alert('Custom clicked'),
      },
    ],
  },
};
