import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LibraryStats } from '@/components/dashboard/LibraryStats'

describe('LibraryStats Component', () => {
  const defaultStats = {
    totalMovies: 150,
    totalTVShows: 50,
    totalEpisodes: 1200,
    totalFiles: 5000,
    totalSize: 1073741824, // 1 GB
    lastUpdated: '2024-01-15T10:00:00Z',
  }

  it('should render all statistics', () => {
    render(<LibraryStats stats={defaultStats} />)

    expect(screen.getByText('150')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
    expect(screen.getByText('1,200')).toBeInTheDocument()
    expect(screen.getByText('5,000')).toBeInTheDocument()
  })

  it('should render labels for each stat', () => {
    render(<LibraryStats stats={defaultStats} />)

    expect(screen.getByText('Movies')).toBeInTheDocument()
    expect(screen.getByText('TV Shows')).toBeInTheDocument()
    expect(screen.getByText('Episodes')).toBeInTheDocument()
    expect(screen.getByText('Total Files')).toBeInTheDocument()
    expect(screen.getByText('Total Size')).toBeInTheDocument()
  })

  it('should format file size correctly', () => {
    render(<LibraryStats stats={defaultStats} />)

    expect(screen.getByText('1 GB')).toBeInTheDocument()
  })

  it('should render zero values correctly', () => {
    render(
      <LibraryStats
        stats={{
          ...defaultStats,
          totalMovies: 0,
          totalTVShows: 0,
          totalEpisodes: 0,
          totalFiles: 0,
          totalSize: 0,
        }}
      />
    )

    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('should apply custom className', () => {
    render(<LibraryStats stats={defaultStats} className="custom-class" />)

    expect(screen.getByTestId('library-stats')).toHaveClass('custom-class')
  })

  it('should show last updated date', () => {
    render(<LibraryStats stats={defaultStats} />)

    expect(screen.getByText(/Updated:/)).toBeInTheDocument()
  })

  it('should render icons for each category', () => {
    render(<LibraryStats stats={defaultStats} />)

    expect(screen.getByTestId('movies-icon')).toBeInTheDocument()
    expect(screen.getByTestId('tvshows-icon')).toBeInTheDocument()
    expect(screen.getByTestId('episodes-icon')).toBeInTheDocument()
    expect(screen.getByTestId('files-icon')).toBeInTheDocument()
    expect(screen.getByTestId('size-icon')).toBeInTheDocument()
  })

  it('should format large numbers with commas', () => {
    const largeStats = {
      ...defaultStats,
      totalMovies: 10000,
      totalFiles: 1000000,
    }

    render(<LibraryStats stats={largeStats} />)

    expect(screen.getByText('10,000')).toBeInTheDocument()
    expect(screen.getByText('1,000,000')).toBeInTheDocument()
  })
})
