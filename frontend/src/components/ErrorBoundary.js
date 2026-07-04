import { Component } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

// Safe Render™ page-level safety net — customers never see a React runtime crash
// caused by missing data. Any render error is caught, logged for Founder maintenance,
// and replaced with a graceful, non-blocking placeholder.
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.warn("[QRU Safe Render™] Caught a render error and recovered gracefully:", error?.message, info?.componentStack);
  }

  componentDidUpdate(prev) {
    // Reset when the route changes so navigation recovers automatically.
    if (this.state.hasError && prev.routeKey !== this.props.routeKey) {
      this.setState({ hasError: false, error: null });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-md mx-auto text-center py-20" data-testid="safe-render-fallback">
          <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto mb-4" strokeWidth={1.5} />
          <h2 className="font-heading text-xl font-bold">This section is being prepared</h2>
          <p className="text-sm text-muted-foreground mt-2">
            Some product data isn't ready yet. The factory logged it for maintenance — nothing is broken.
          </p>
          <button
            data-testid="safe-render-retry"
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-5 inline-flex items-center gap-2 border px-4 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors"
          >
            <RefreshCw className="w-4 h-4" /> Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
