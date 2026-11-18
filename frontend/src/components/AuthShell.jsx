import { CheckIcon } from './Icons.jsx';

export default function AuthShell({ children }) {
  return (
    <div className="auth-page">
      <div className="auth-shell">
        <div className="brand auth-brand">
          <span className="brand-mark">
            <CheckIcon size={17} strokeWidth={2.6} />
          </span>
          <div>
            <h1>Lavender</h1>
            <p>Task Manager</p>
          </div>
        </div>

        <main className="auth-card">{children}</main>
        <p className="auth-footnote">A calm place to get things done.</p>
      </div>
    </div>
  );
}
