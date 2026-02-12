import React from 'react'
import { Link } from 'react-router-dom'
import { FaFolder, FaSearch, FaTv, FaFilm, FaChartBar, FaArrowRight } from 'react-icons/fa'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { EmptyState } from '@/components/common/EmptyState'

const features = [
  {
    icon: <FaFolder className="w-8 h-8" />,
    title: 'File Management',
    description: 'Browse, organize, and manage your files with ease',
    link: '/files',
  },
  {
    icon: <FaSearch className="w-8 h-8" />,
    title: 'Advanced Search',
    description: 'Find files quickly with powerful search and filtering',
    link: '/search',
  },
  {
    icon: <FaFilm className="w-8 h-8" />,
    title: 'Movies',
    description: 'Explore and manage your movie collection',
    link: '/movies',
  },
  {
    icon: <FaTv className="w-8 h-8" />,
    title: 'TV Shows',
    description: 'Organize and track your favorite TV series',
    link: '/tv-shows',
  },
  {
    icon: <FaChartBar className="w-8 h-8" />,
    title: 'Dashboard',
    description: 'View statistics and insights about your library',
    link: '/dashboard',
  },
]

export const HomePage: React.FC = () => {
  const handleGetStarted = () => {
    window.location.href = '/files'
  }

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-4xl sm:text-5xl font-bold text-secondary-900 dark:text-white mb-4">
          Welcome to Metamaster
        </h1>
        <p className="text-xl text-secondary-600 dark:text-secondary-400 mb-8 max-w-2xl mx-auto">
          Your powerful media management and file navigation tool. Organize, search, and manage your digital library with ease.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            variant="primary"
            size="lg"
            onClick={handleGetStarted}
            rightIcon={<FaArrowRight />}
          >
            Get Started
          </Button>
          <Link to="/dashboard">
            <Button variant="secondary" size="lg">
              View Dashboard
            </Button>
          </Link>
        </div>
      </section>

      {/* Features Grid */}
      <section>
        <h2 className="text-3xl font-bold text-secondary-900 dark:text-white mb-8 text-center">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Link key={index} to={feature.link}>
              <Card
                variant="bordered"
                hoverable
                className="p-6 h-full transition-all duration-200 hover:shadow-md"
              >
                <div className="text-primary-500 mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold text-secondary-900 dark:text-white mb-2">{feature.title}</h3>
                <p className="text-secondary-600 dark:text-secondary-400 text-sm">{feature.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Quick Stats - Uses Empty State pattern instead of hardcoded 0 */}
      <Card variant="bordered" className="p-8">
        <h2 className="text-2xl font-bold text-secondary-900 dark:text-white mb-6">Quick Stats</h2>
        <EmptyState
          iconVariant="noData"
          title="Nothing here, yet"
          description="Configure your media library to see statistics"
          action={{
            label: 'Configure Library',
            onClick: () => window.location.href = '/settings?section=paths',
            variant: 'secondary',
          }}
          className="py-8"
        />
      </Card>

      {/* CTA Section */}
      <Card variant="elevated" className="bg-secondary-900 p-8 text-center">
        <h2 className="text-2xl font-bold text-white mb-4">Ready to get started?</h2>
        <p className="text-secondary-300 mb-6">
          Start managing your media library today with Metamaster.
        </p>
        <Button
          variant="primary"
          size="lg"
          onClick={handleGetStarted}
          rightIcon={<FaArrowRight />}
        >
          Browse Files
        </Button>
      </Card>
    </div>
  )
}
