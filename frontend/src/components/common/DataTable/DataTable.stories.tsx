import type { Meta, StoryObj } from '@storybook/react'
import { DataTable } from './DataTable'
import type { Column, DataTableProps } from './DataTable'

const meta: Meta<typeof DataTable> = {
  title: 'Components/DataTable',
  component: DataTable,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  args: {
    columns: [],
    data: [],
    keyExtractor: (row: unknown) => String(row),
  },
}

export default meta
type Story = StoryObj<typeof DataTable>

interface User {
  id: string
  name: string
  email: string
  role: string
  status: string
}

const columns: Column<User>[] = [
  { key: 'name', header: 'Name', sortable: true },
  { key: 'email', header: 'Email', sortable: true },
  { key: 'role', header: 'Role', sortable: true },
  {
    key: 'status',
    header: 'Status',
    render: (row: User) => (
      <span
        className={`px-2 py-1 text-xs rounded-full ${
          row.status === 'active'
            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
        }`}
      >
        {row.status}
      </span>
    ),
  },
]

const data: User[] = [
  { id: '1', name: 'John Doe', email: 'john@example.com', role: 'Admin', status: 'active' },
  { id: '2', name: 'Jane Smith', email: 'jane@example.com', role: 'User', status: 'active' },
  { id: '3', name: 'Bob Johnson', email: 'bob@example.com', role: 'User', status: 'inactive' },
  { id: '4', name: 'Alice Brown', email: 'alice@example.com', role: 'Editor', status: 'active' },
  { id: '5', name: 'Charlie Wilson', email: 'charlie@example.com', role: 'User', status: 'inactive' },
]

export const Default: Story = {
  args: {
    columns: columns as unknown as Column<unknown>[],
    data: data as unknown[],
    keyExtractor: ((row: unknown) => (row as User).id) as (row: unknown) => string,
  },
}

export const WithSorting: Story = {
  args: {
    columns: columns as unknown as Column<unknown>[],
    data: data as unknown[],
    keyExtractor: ((row: unknown) => (row as User).id) as (row: unknown) => string,
    sortColumn: 'name',
    sortDirection: 'asc',
    onSort: (column: string, direction: 'asc' | 'desc') => console.log('Sort:', column, direction),
  },
}

export const WithPagination: Story = {
  args: {
    columns: columns as unknown as Column<unknown>[],
    data: data as unknown[],
    keyExtractor: ((row: unknown) => (row as User).id) as (row: unknown) => string,
    pagination: {
      page: 1,
      pageSize: 3,
      total: 25,
      onPageChange: (page: number) => console.log('Page:', page),
    },
  },
}

export const WithRowSelection: Story = {
  args: {
    columns: columns as unknown as Column<unknown>[],
    data: data as unknown[],
    keyExtractor: ((row: unknown) => (row as User).id) as (row: unknown) => string,
    rowSelection: {
      selectedKeys: ['1', '3'],
      onSelectionChange: (keys: string[]) => console.log('Selected:', keys),
    },
  },
}

export const WithRowClick: Story = {
  args: {
    columns: columns as unknown as Column<unknown>[],
    data: data as unknown[],
    keyExtractor: ((row: unknown) => (row as User).id) as (row: unknown) => string,
    onRowClick: (row: unknown) => alert(`Clicked: ${(row as User).name}`),
  },
}

export const Loading: Story = {
  args: {
    columns: columns as unknown as Column<unknown>[],
    data: [] as unknown[],
    keyExtractor: ((row: unknown) => (row as User).id) as (row: unknown) => string,
    loading: true,
  },
}

export const Empty: Story = {
  args: {
    columns: columns as unknown as Column<unknown>[],
    data: [] as unknown[],
    keyExtractor: ((row: unknown) => (row as User).id) as (row: unknown) => string,
  },
}

export const AllFeatures: Story = {
  args: {
    columns: columns as unknown as Column<unknown>[],
    data: data as unknown[],
    keyExtractor: ((row: unknown) => (row as User).id) as (row: unknown) => string,
    sortColumn: 'name',
    sortDirection: 'asc',
    pagination: {
      page: 1,
      pageSize: 3,
      total: 5,
      onPageChange: (page: number) => console.log('Page:', page),
    },
    rowSelection: {
      selectedKeys: [],
      onSelectionChange: (keys: string[]) => console.log('Selected:', keys),
    },
    onRowClick: (row: unknown) => console.log('Clicked:', row),
  },
}

export const DarkMode: Story = {
  args: {
    columns: columns as unknown as Column<unknown>[],
    data: data as unknown[],
    keyExtractor: ((row: unknown) => (row as User).id) as (row: unknown) => string,
  },
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
}
