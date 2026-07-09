import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  label?: string;
}

interface State {
  error: Error | null;
}

// Aísla el fallo de un subárbol para no desmontar toda la app.
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`[ErrorBoundary${this.props.label ? `:${this.props.label}` : ""}]`, error, info);
  }

  render() {
    if (this.state.error) {
      if (this.props.fallback !== undefined) return this.props.fallback;
      return (
        <div className="flex h-full w-full items-center justify-center p-6">
          <div className="max-w-lg rounded-md border border-fuchsia-400/40 bg-black/70 p-5 font-mono text-sm text-fuchsia-200 backdrop-blur">
            <p className="mb-2 tracking-widest text-fuchsia-300">// FALLO DE INTERFAZ</p>
            <p className="text-cyan-100/80">
              Ocurrió un error al renderizar. Recarga la página; si persiste, revisa la consola.
            </p>
            <pre className="mt-3 overflow-auto whitespace-pre-wrap text-xs text-fuchsia-300/70">
              {this.state.error.message}
            </pre>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
