import { SearchIcon, XIcon } from './Icons.jsx';

const FILTERS = [
  { key: 'all', label: 'All', countKey: 'total' },
  { key: 'pending', label: 'Pending', countKey: 'pending' },
  { key: 'completed', label: 'Completed', countKey: 'completed' },
];

export default function TaskToolbar({ filter, onFilter, search, onSearch, stats }) {
  return (
    <div className="toolbar">
      <div className="filter-tabs" role="group" aria-label="Filter tasks">
        {FILTERS.map(({ key, label, countKey }) => (
          <button
            key={key}
            type="button"
            className={`filter-tab ${filter === key ? 'is-active' : ''}`}
            onClick={() => onFilter(key)}
            aria-pressed={filter === key}
          >
            {label}
            <span className="filter-count">{stats[countKey] ?? 0}</span>
          </button>
        ))}
      </div>

      <div className="search-field">
        <SearchIcon size={15} />
        <input
          type="search"
          value={search}
          onChange={(event) => onSearch(event.target.value)}
          placeholder="Search tasks…"
          aria-label="Search tasks"
        />
        {search && (
          <button
            type="button"
            className="search-clear"
            onClick={() => onSearch('')}
            aria-label="Clear search"
          >
            <XIcon size={13} />
          </button>
        )}
      </div>
    </div>
  );
}
