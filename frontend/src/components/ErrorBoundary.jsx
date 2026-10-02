import React from 'react';

// Per-panel error boundary. The app previously had NO boundary anywhere —
// one render error (e.g. an undefined identifier or a malformed API payload)
// unmounted the entire app and presented as a "frozen" page.
//
// Wrap tab content with a resetKey tied to the current route so switching
// tabs/sections remounts the crashed subtree without a full page reload.
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error(`[ErrorBoundary] ${this.props.label || 'panel'} crashed:`, error, info);
  }

  componentDidUpdate(prevProps) {
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="qr-surface p-6 border-l-2 border-l-rose-500">
          <div className="text-sm font-bold text-rose-400 mb-1">This panel crashed</div>
          <p className="text-xs text-slate-400 mb-3">
            {this.props.label ? `The ${this.props.label} view hit a render error` : 'A render error occurred'}
            {' '}({String(this.state.error?.message || this.state.error)}).
            Switch tabs to retry — the rest of the app is unaffected.
          </p>
          <button
            onClick={() => this.setState({ error: null })}
            className="qr-btn-primary"
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
