import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import ConfirmDialog from '../ConfirmDialog';
import ErrorAlert from '../ErrorAlert';
import LoadingSpinner from '../LoadingSpinner';
import PageLayout from '../PageLayout';

describe('LoadingSpinner', () => {
  it('renders without crashing', () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows message when provided', () => {
    render(<LoadingSpinner message="Loading data..." />);
    expect(screen.getByText('Loading data...')).toBeInTheDocument();
  });
});

describe('ErrorAlert', () => {
  it('renders error message', () => {
    render(<ErrorAlert message="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('shows close button when onClose provided', () => {
    const onClose = vi.fn();
    render(<ErrorAlert message="Error" onClose={onClose} />);
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });
});

describe('ConfirmDialog', () => {
  it('renders title and message when open', () => {
    render(
      <ConfirmDialog
        open={true}
        title="Delete Item"
        message="Are you sure?"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByText('Delete Item')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('renders Cancel and Confirm buttons', () => {
    render(
      <ConfirmDialog
        open={true}
        title="Delete"
        message="Confirm?"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
  });
});

describe('PageLayout', () => {
  it('renders children', () => {
    render(
      <PageLayout>
        <div>Page content</div>
      </PageLayout>,
    );
    expect(screen.getByText('Page content')).toBeInTheDocument();
  });

  it('renders default title', () => {
    render(
      <PageLayout>
        <div />
      </PageLayout>,
    );
    expect(screen.getByText('GenHealth AI')).toBeInTheDocument();
  });

  it('renders user name and logout button', () => {
    const onLogout = vi.fn();
    render(
      <PageLayout user={{ first_name: 'John', last_name: 'Doe' }} onLogout={onLogout}>
        <div />
      </PageLayout>,
    );
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Logout' })).toBeInTheDocument();
  });
});
