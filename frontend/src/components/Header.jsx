import { CheckIcon, PlusIcon } from './Icons.jsx';

export default function Header({ onNewTask }) {
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

      <button type="button" className="btn btn-primary" onClick={onNewTask}>
        <PlusIcon size={16} strokeWidth={2.2} />
        New task
      </button>
    </header>
  );
}
