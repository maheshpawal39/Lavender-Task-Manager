import { CheckCircleIcon, ClockIcon, ListIcon } from './Icons.jsx';

const ITEMS = [
  { key: 'all', valueKey: 'total', label: 'Total tasks', icon: ListIcon },
  { key: 'pending', valueKey: 'pending', label: 'Pending', icon: ClockIcon },
  { key: 'completed', valueKey: 'completed', label: 'Completed', icon: CheckCircleIcon },
];

export default function StatsBoard({ stats, activeFilter, onFilter }) {
  return (
    <section className="stats-grid" aria-label="Task overview">
      {ITEMS.map(({ key, valueKey, label, icon: Icon }) => (
        <button
          key={key}
          type="button"
          className={`stat-card ${activeFilter === key ? 'is-active' : ''}`}
          onClick={() => onFilter(key)}
          aria-pressed={activeFilter === key}
        >
          <span className={`stat-icon ${key}`}>
            <Icon size={17} />
          </span>
          <span className="stat-copy">
            <span className="stat-value">{stats[valueKey] ?? 0}</span>
            <span className="stat-label">{label}</span>
          </span>
        </button>
      ))}
    </section>
  );
}
