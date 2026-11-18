import { useState } from 'react';
import { dueDateInfo } from '../utils/date.js';
import { CalendarIcon, CheckIcon, PencilIcon, TrashIcon } from './Icons.jsx';

export default function TaskCard({ task, onToggle, onEdit, onDelete }) {
  const [busy, setBusy] = useState(false);
  const completed = task.status === 'completed';
  const due = dueDateInfo(task.due_date, task.status);

  async function handleToggle() {
    setBusy(true);
    try {
      await onToggle(task);
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className={`task-card ${completed ? 'is-completed' : ''}`}>
      <button
        type="button"
        className="task-check"
        onClick={handleToggle}
        disabled={busy}
        aria-label={completed ? `Mark “${task.title}” as pending` : `Mark “${task.title}” as completed`}
        aria-pressed={completed}
      >
        <CheckIcon size={13} strokeWidth={2.8} />
      </button>

      <div className="task-main">
        <h3 className="task-title">{task.title}</h3>
        {task.description && <p className="task-description">{task.description}</p>}
        <div className="task-meta">
          {due && (
            <span className={`due-chip ${due.overdue ? 'is-overdue' : ''}`} title={due.title}>
              <CalendarIcon size={12} />
              {due.label}
            </span>
          )}
          <span className={`status-pill ${completed ? 'completed' : 'pending'}`}>
            {completed ? 'Completed' : 'Pending'}
          </span>
        </div>
      </div>

      <div className="task-actions">
        <button
          type="button"
          className="icon-btn"
          onClick={() => onEdit(task)}
          aria-label={`Edit “${task.title}”`}
          title="Edit task"
        >
          <PencilIcon size={15} />
        </button>
        <button
          type="button"
          className="icon-btn danger"
          onClick={() => onDelete(task)}
          aria-label={`Delete “${task.title}”`}
          title="Delete task"
        >
          <TrashIcon size={15} />
        </button>
      </div>
    </article>
  );
}
