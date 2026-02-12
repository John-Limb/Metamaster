import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Skeleton, SkeletonText, SkeletonAvatar, SkeletonCard, SkeletonTable, SkeletonMovieCard, SkeletonTVShowCard, SkeletonStatCard } from '@/components/common/Skeleton'

describe('Skeleton Components', () => {
  describe('Skeleton', () => {
    it('renders skeleton with default props', () => {
      render(<Skeleton />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton).toHaveClass('bg-secondary-200')
    })

    it('renders text variant', () => {
      render(<Skeleton variant="text" width="100%" />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton).toHaveClass('rounded')
    })

    it('renders circular variant', () => {
      render(<Skeleton variant="circular" width={48} height={48} />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton).toHaveClass('rounded-full')
    })

    it('renders rectangular variant', () => {
      render(<Skeleton variant="rectangular" width={200} height={100} />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton).toHaveClass('rounded-none')
    })

    it('applies shimmer animation by default', () => {
      render(<Skeleton />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toHaveClass('animate-shimmer')
    })

    it('supports pulse animation', () => {
      render(<Skeleton animation="pulse" />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toHaveClass('animate-pulse')
    })

    it('supports no animation', () => {
      render(<Skeleton animation="none" />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).not.toHaveClass('animate-pulse')
      expect(skeleton).not.toHaveClass('animate-shimmer')
    })

    it('applies custom className', () => {
      render(<Skeleton className="custom-skeleton" />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toHaveClass('custom-skeleton')
    })

    it('has aria-label for screen readers', () => {
      render(<Skeleton />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toHaveAttribute('aria-label', 'Loading...')
    })
  })

  describe('SkeletonText', () => {
    it('renders multiple lines of text', () => {
      render(<SkeletonText lines={4} />)
      const skeletons = screen.getAllByRole('status')
      expect(skeletons).toHaveLength(4)
    })

    it('renders last line shorter', () => {
      render(<SkeletonText lines={3} />)
      const skeletons = screen.getAllByRole('status')
      expect(skeletons[2]).toHaveStyle({ width: '60%' })
    })

    it('applies container className', () => {
      render(<SkeletonText className="text-container" />)
      const container = screen.getByText('').parentElement
      expect(container).toHaveClass('text-container')
    })
  })

  describe('SkeletonAvatar', () => {
    it('renders circular avatar with specified size', () => {
      render(<SkeletonAvatar size={48} />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toHaveClass('rounded-full')
      expect(skeleton).toHaveStyle({ width: '48px', height: '48px' })
    })

    it('uses default size of 40', () => {
      render(<SkeletonAvatar />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toHaveStyle({ width: '40px', height: '40px' })
    })
  })

  describe('SkeletonCard', () => {
    it('renders card skeleton with avatar and text', () => {
      render(<SkeletonCard />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton).toHaveClass('space-y-4')
    })
  })

  describe('SkeletonTable', () => {
    it('renders table skeleton with rows and columns', () => {
      render(<SkeletonTable rows={5} columns={4} />)
      const skeletons = screen.getAllByRole('status')
      // 1 header row + 5 data rows
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('can hide header', () => {
      render(<SkeletonTable rows={5} columns={3} showHeader={false} />)
      const skeletons = screen.getAllByRole('status')
      expect(skeletons.length).toBe(5)
    })
  })

  describe('SkeletonMovieCard', () => {
    it('renders movie card skeleton with poster placeholder', () => {
      render(<SkeletonMovieCard />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton).toHaveClass('rounded-lg')
    })

    it('has aria-label for loading movie card', () => {
      render(<SkeletonMovieCard />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toHaveAttribute('aria-label', 'Loading movie card')
    })
  })

  describe('SkeletonTVShowCard', () => {
    it('renders TV show card skeleton', () => {
      render(<SkeletonTVShowCard />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton).toHaveAttribute('aria-label', 'Loading TV show card')
    })
  })

  describe('SkeletonStatCard', () => {
    it('renders stat card skeleton', () => {
      render(<SkeletonStatCard />)
      const skeleton = screen.getByRole('status')
      expect(skeleton).toBeInTheDocument()
      expect(skeleton).toHaveAttribute('aria-label', 'Loading stat card')
    })
  })
})
