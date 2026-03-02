import js from '@eslint/js'
import globals from 'globals'
import reactPlugin from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import securityPlugin from 'eslint-plugin-security'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      security: securityPlugin,
      react: reactPlugin,
    },
    rules: {
      // Security rules (only those provided by eslint-plugin-security@3)
      'security/detect-unsafe-regex': 'error',
      'security/detect-possible-timing-attacks': 'error',
      'security/detect-non-literal-fs-filename': 'error',
      'security/detect-no-csrf-before-method-override': 'error',
      'security/detect-eval-with-expression': 'error',
      'security/detect-buffer-noassert': 'error',
      'security/detect-child-process': 'error',
      'security/detect-new-buffer': 'error',
      'security/detect-non-literal-regexp': 'error',
      'security/detect-non-literal-require': 'error',
      'security/detect-object-injection': 'warn',

      // React security
      'react/no-danger': 'error',
      'react/no-danger-with-children': 'error',
      'react/iframe-missing-sandbox': 'error',
      'react/no-direct-mutation-state': 'error',
      'react/react-in-jsx-scope': 'off',
    },
  },
])
