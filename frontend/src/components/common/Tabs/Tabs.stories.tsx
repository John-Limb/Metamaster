import type { Meta, StoryObj } from '@storybook/react'
import { Tabs } from './Tabs'

const meta: Meta<typeof Tabs> = {
  title: 'Components/Tabs',
  component: Tabs,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'pills'],
    },
  },
}

export default meta
type Story = StoryObj<typeof Tabs>

const tabs = [
  { id: 'tab1', label: 'Overview' },
  { id: 'tab2', label: 'Features' },
  { id: 'tab3', label: 'Pricing' },
  { id: 'tab4', label: 'Disabled', disabled: true },
]

const tabsWithIcons = [
  {
    id: 'home',
    label: 'Home',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
      </svg>
    ),
  },
  {
    id: 'profile',
    label: 'Profile',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
      </svg>
    ),
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
]

export const Default: Story = {
  args: {
    tabs,
    activeTab: 'tab1',
    onChange: (tabId) => console.log('Tab:', tabId),
    children: <div className="p-4 bg-white dark:bg-secondary-800 rounded-lg">Tab content</div>,
  },
}

export const Pills: Story = {
  args: {
    tabs,
    activeTab: 'tab1',
    variant: 'pills',
    onChange: (tabId) => console.log('Tab:', tabId),
    children: <div className="p-4 bg-white dark:bg-secondary-800 rounded-lg">Tab content</div>,
  },
}

export const WithIcons: Story = {
  args: {
    tabs: tabsWithIcons,
    activeTab: 'home',
    onChange: (tabId) => console.log('Tab:', tabId),
    children: <div className="p-4 bg-white dark:bg-secondary-800 rounded-lg">Tab content</div>,
  },
}

export const DisabledTab: Story = {
  args: {
    tabs,
    activeTab: 'tab1',
    onChange: (tabId) => console.log('Tab:', tabId),
    children: <div className="p-4 bg-white dark:bg-secondary-800 rounded-lg">Tab content</div>,
  },
}

export const DarkMode: Story = {
  args: {
    tabs,
    activeTab: 'tab1',
    variant: 'pills',
    onChange: (tabId) => console.log('Tab:', tabId),
    children: <div className="p-4 bg-secondary-800 rounded-lg">Tab content</div>,
  },
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
