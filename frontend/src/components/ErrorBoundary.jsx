import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 my-6 text-center rounded-2xl bg-slate-900/90 border border-rose-500/30 shadow-xl max-w-xl mx-auto">
          <div className="w-12 h-12 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-white font-outfit mb-1">
            {this.props.title || 'এই বিভাগটি লোড হতে সমস্যা হয়েছে (Unable to load section)'}
          </h3>
          <p className="text-xs text-slate-400 mb-5 leading-relaxed">
            {this.state.error?.message || 'সাময়িক ডাটা প্রসেসিং জটিলতার কারণে তথ্য রেন্ডার করা যায়নি।'}
          </p>
          <button
            onClick={this.handleReset}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-950/40 transition-all border border-emerald-500/40"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>আবার চেষ্টা করুন (Retry)</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
