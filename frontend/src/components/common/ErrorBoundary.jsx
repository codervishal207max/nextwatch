import { Component } from "react";

// Shows the real error on the page (message and file/line) instead of a blank screen.
export default class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    const text = String(error?.stack || error?.message || error);
    return (
      <div className="m-6 rounded-xl border border-red-500/40 bg-red-500/10 p-5 text-red-200" role="alert">
        <p className="font-semibold">Something broke on this page.</p>
        <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap text-xs">{text}</pre>
        <button
          onClick={() => window.location.assign("/")}
          className="mt-4 rounded-lg border border-red-400/50 px-4 py-2 text-sm hover:bg-red-500/20"
        >
          Go to Home
        </button>
      </div>
    );
  }
}