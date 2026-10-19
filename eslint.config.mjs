import prettier from 'eslint-config-prettier';
import globals from 'globals';

export default [
  {
    ignores: [
      'main/static/dev/**',
      'main/static/min/**',
      'main/static/ext/**',
      'node_modules/**',
      '.venv/**',
      'ds-data/**',
    ],
  },
  prettier,
  {
    files: ['**/*.js'],
    languageOptions: {
      ecmaVersion: 2017,
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      curly: 'error',
      'dot-notation': 'error',
      'id-length': 'error',
      'no-const-assign': 'error',
      'no-dupe-class-members': 'error',
      'no-else-return': 'error',
      'no-inner-declarations': 'error',
      'no-lonely-if': 'error',
      'no-shadow': 'error',
      'no-unneeded-ternary': 'error',
      'no-unused-expressions': 'error',
      'no-unused-vars': ['error', {args: 'none'}],
      'no-useless-return': 'error',
      'no-var': 'error',
      'one-var': ['error', 'never'],
      'prefer-arrow-callback': 'error',
      'prefer-const': 'error',
      'prefer-promise-reject-errors': 'error',
      'sort-imports': 'error',
      'sort-keys': ['error', 'asc', {caseSensitive: true, natural: true}],
      'sort-vars': 'error',
      strict: ['error', 'global'],
    },
  },
];
