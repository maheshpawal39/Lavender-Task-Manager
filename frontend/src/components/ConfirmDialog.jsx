import useModalBehavior from '../hooks/useModalBehavior.js';
import { TrashIcon } from './Icons.jsx';

export default function ConfirmDialog({ task, busy, onCancel, onConfirm }) {
  useModalBehavior(onCancel, !busy);

  return (
    <div
      className="modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !busy) onCancel();
      }}
    >
      <div
        className="modal confirm-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
      >
        <span className="confirm-icon">
          <TrashIcon size={20} />
        </span>
        <h2 id="confirm-title">Delete this task?</h2>
        <p>
          “{task.title}” will be removed permanently. This can’t be undone.
        </p>
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button type="button" className="btn btn-danger" onClick={onConfirm} disabled={busy}>
            {busy ? 'Deleting…' : 'Delete task'}
          </button>
        </div>
      </div>
    </div>
  );
}
