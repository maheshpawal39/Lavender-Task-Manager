import { ListIcon, PlusIcon } from './Icons.jsx';

export default function EmptyState({ hasSearch, filter, onAdd }) {
  let title = 'No tasks here yet';
  let message = 'Add a task and give your day a little shape.';

  if (hasSearch) {
    title = 'No matching tasks';
    message = 'Try a different word, or clear the search to see everything.';
  } else if (filter === 'pending') {
    title = 'All caught up';
    message = 'Nothing is waiting for you. Enjoy the quiet.';
  } else if (filter === 'completed') {
    title = 'Nothing completed yet';
    message = 'Finished tasks will collect here.';
  }

  return (
    <div className="empty-state">
      <span className="empty-icon">
        <ListIcon size={20} />
      </span>
      <h3>{title}</h3>
      <p>{message}</p>
      {!hasSearch && filter !== 'completed' && (
        <button type="button" className="btn btn-soft" onClick={onAdd}>
          <PlusIcon size={15} />
          Add a task
        </button>
      )}
    </div>
  );
}
