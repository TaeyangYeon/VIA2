import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import EngineSetupGuide from '../components/EngineSetupGuide';

const defaultProps = {
  isOpen: true,
  engineMode: 'local' as const,
  onClose: jest.fn(),
  onRetry: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
});

describe('EngineSetupGuide rendering', () => {
  it('renders when isOpen is true', () => {
    render(<EngineSetupGuide {...defaultProps} />);
    expect(screen.getByTestId('engine-setup-guide')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<EngineSetupGuide {...defaultProps} isOpen={false} />);
    expect(screen.queryByTestId('engine-setup-guide')).not.toBeInTheDocument();
  });

  it('renders data-testid engine-setup-guide', () => {
    render(<EngineSetupGuide {...defaultProps} />);
    expect(screen.getByTestId('engine-setup-guide')).toBeInTheDocument();
  });

  it('renders data-testid engine-setup-retry-btn', () => {
    render(<EngineSetupGuide {...defaultProps} />);
    expect(screen.getByTestId('engine-setup-retry-btn')).toBeInTheDocument();
  });

  it('renders data-testid engine-setup-continue-btn', () => {
    render(<EngineSetupGuide {...defaultProps} />);
    expect(screen.getByTestId('engine-setup-continue-btn')).toBeInTheDocument();
  });

  it('renders data-testid engine-setup-mode-label', () => {
    render(<EngineSetupGuide {...defaultProps} />);
    expect(screen.getByTestId('engine-setup-mode-label')).toBeInTheDocument();
  });
});

describe('local mode', () => {
  it('shows Ollama install step', () => {
    render(<EngineSetupGuide {...defaultProps} engineMode="local" />);
    expect(screen.getByText('brew install ollama')).toBeInTheDocument();
  });

  it('shows ollama serve step', () => {
    render(<EngineSetupGuide {...defaultProps} engineMode="local" />);
    expect(screen.getByText('ollama serve')).toBeInTheDocument();
  });

  it('shows model pull step', () => {
    render(<EngineSetupGuide {...defaultProps} engineMode="local" />);
    expect(screen.getByText('ollama pull qwen2.5-coder:7b')).toBeInTheDocument();
  });

  it('displays mode label as local', () => {
    render(<EngineSetupGuide {...defaultProps} engineMode="local" />);
    expect(screen.getByTestId('engine-setup-mode-label')).toHaveTextContent('local');
  });
});

describe('remote mode', () => {
  it('shows remote URL when engineMode is remote', () => {
    render(
      <EngineSetupGuide
        {...defaultProps}
        engineMode="remote"
        remoteUrl="https://my-engine.example.com"
      />
    );
    expect(screen.getByDisplayValue('https://my-engine.example.com')).toBeInTheDocument();
  });

  it('shows text input for URL editing in remote mode', () => {
    render(
      <EngineSetupGuide
        {...defaultProps}
        engineMode="remote"
        remoteUrl="http://remote-host"
      />
    );
    expect(screen.getByPlaceholderText('https://your-engine-url/...')).toBeInTheDocument();
  });

  it('displays mode label as remote', () => {
    render(
      <EngineSetupGuide {...defaultProps} engineMode="remote" remoteUrl="http://x" />
    );
    expect(screen.getByTestId('engine-setup-mode-label')).toHaveTextContent('remote');
  });

  it('does not show ollama instructions in remote mode', () => {
    render(
      <EngineSetupGuide {...defaultProps} engineMode="remote" remoteUrl="http://x" />
    );
    expect(screen.queryByText('brew install ollama')).not.toBeInTheDocument();
  });
});

describe('button interactions', () => {
  it('calls onRetry when Retry button is clicked', () => {
    const onRetry = jest.fn();
    render(<EngineSetupGuide {...defaultProps} onRetry={onRetry} />);
    fireEvent.click(screen.getByTestId('engine-setup-retry-btn'));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Continue Anyway button is clicked', () => {
    const onClose = jest.fn();
    render(<EngineSetupGuide {...defaultProps} onClose={onClose} />);
    fireEvent.click(screen.getByTestId('engine-setup-continue-btn'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('Continue Anyway button text is correct', () => {
    render(<EngineSetupGuide {...defaultProps} />);
    expect(screen.getByTestId('engine-setup-continue-btn')).toHaveTextContent('Continue Anyway');
  });

  it('Retry button text is correct', () => {
    render(<EngineSetupGuide {...defaultProps} />);
    expect(screen.getByTestId('engine-setup-retry-btn')).toHaveTextContent('Retry');
  });
});
