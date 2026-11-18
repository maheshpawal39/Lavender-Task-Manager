import { CheckIcon, LogOutIcon, PlusIcon } from './Icons.jsx';

function initials(name = '') {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('');
}

export default function Header({ onNewTask, user, onLogout }) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark">
          <CheckIcon size={17} strokeWidth={2.6} />
        </span>
        <div>
          <h1>Lavender</h1>
          <p>Task Manager</p>
        </div>
      </div>

      <div className="header-actions">
        {user && (
          <div className="user-chip" title={user.email}>
            <span className="user-avatar">{initials(user.full_name)}</span>
            <span className="user-name">{user.full_name.split(/\s+/)[0]}</span>
          </div>
        )}

        <button type="button" className="btn btn-primary" onClick={onNewTask}>
          <PlusIcon size={16} strokeWidth={2.2} />
          New task
        </button>

        <button
          type="button"
          className="icon-btn header-logout"
          onClick={onLogout}
          aria-label="Sign out"
          title="Sign out"
        >
          <LogOutIcon size={16} />
        </button>
      </div>
    </header>
  );
}
