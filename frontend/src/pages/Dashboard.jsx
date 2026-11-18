import { useCallback, useEffect, useState } from 'react';
import { taskApi } from '../api.js';
import ConfirmDialog from '../components/ConfirmDialog.jsx';
import EmptyState from '../components/EmptyState.jsx';
import Header from '../components/Header.jsx';
import StatsBoard from '../components/StatsBoard.jsx';
import TaskCard from '../components/TaskCard.jsx';
import TaskFormModal from '../components/TaskFormModal.jsx';
import TaskToolbar from '../components/TaskToolbar.jsx';
import Toast from '../components/Toast.jsx';

const EMPTY_STATS = { total: 0, pending: 0, completed: 0 };

export default function Dashboard({ user, onLogout }) {
  const [tasks, setTasks] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  const [modal, setModal] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 250);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const [list, summary] = await Promise.all([
          taskApi.list({ status: filter, search: debouncedSearch }),
          taskApi.stats(),
        ]);
        if (controller.signal.aborted) return;
        setTasks(list.tasks);
        setStats(summary);
        setError('');
      } catch (requestError) {
        if (!controller.signal.aborted) setError(requestError.message);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [filter, debouncedSearch, reloadKey]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = setTimeout(() => setToast(null), 2800);
    return () => clearTimeout(timer);
  }, [toast]);

  const refresh = useCallback(() => setReloadKey((key) => key + 1), []);

  const closeModal = useCallback(() => setModal(null), []);

  async function handleSave(payload) {
    const isEdit = modal.mode === 'edit';

    if (isEdit) {
      await taskApi.update(modal.task.id, payload);
    } else {
      const data = await taskApi.create(payload);
      const created = data.task;
      const term = debouncedSearch.trim().toLowerCase();
      const matchesSearch =
        !term ||
        created.title.toLowerCase().includes(term) ||
        created.description.toLowerCase().includes(term);
      const matchesFilter = filter === 'all' || filter === created.status;

      // Show the saved task immediately; the refresh below keeps counts in sync.
      if (matchesSearch && matchesFilter) {
        setTasks((current) => [created, ...current]);
      }
      setStats((current) => ({
        ...current,
        total: current.total + 1,
        [created.status]: current[created.status] + 1,
      }));
    }

    setModal(null);
    setToast({ message: isEdit ? 'Task updated' : 'Task added', tone: 'success' });
    refresh();
  }

  async function handleToggle(task) {
    const nextStatus = task.status === 'pending' ? 'completed' : 'pending';

    setTasks((current) => {
      const updated = current.map((item) =>
        item.id === task.id ? { ...item, status: nextStatus } : item,
      );
      if (filter !== 'all' && filter !== nextStatus) {
        return updated.filter((item) => item.id !== task.id);
      }
      return updated;
    });

    setStats((current) => ({
      ...current,
      pending: current.pending + (nextStatus === 'pending' ? 1 : -1),
      completed: current.completed + (nextStatus === 'completed' ? 1 : -1),
    }));

    try {
      await taskApi.update(task.id, { status: nextStatus });
      setToast({
        message: nextStatus === 'completed' ? 'Task completed' : 'Task moved back to pending',
        tone: 'success',
      });
    } catch (requestError) {
      setToast({ message: requestError.message, tone: 'error' });
      refresh();
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await taskApi.remove(deleteTarget.id);
      setToast({ message: 'Task deleted', tone: 'success' });
      setDeleteTarget(null);
      refresh();
    } catch (requestError) {
      setToast({ message: requestError.message, tone: 'error' });
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  }

  const hasSearch = debouncedSearch.trim().length > 0;

  return (
    <div className="page">
      <div className="app-shell">
        <Header
          user={user}
          onLogout={onLogout}
          onNewTask={() => setModal({ mode: 'create' })}
        />

        <main>
          <StatsBoard stats={stats} activeFilter={filter} onFilter={setFilter} />

          <section className="task-panel" aria-label="Tasks">
            <TaskToolbar
              filter={filter}
              onFilter={setFilter}
              search={search}
              onSearch={setSearch}
              stats={stats}
            />

            {error && (
              <div className="error-banner" role="alert">
                <span>{error}</span>
                <button type="button" className="btn btn-ghost btn-sm" onClick={refresh}>
                  Retry
                </button>
              </div>
            )}

            <div className="task-list" aria-busy={loading}>
              {loading ? (
                <div className="loading-state">
                  <span className="spinner" aria-hidden="true" />
                  Loading tasks…
                </div>
              ) : tasks.length > 0 ? (
                tasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onToggle={handleToggle}
                    onEdit={(item) => setModal({ mode: 'edit', task: item })}
                    onDelete={setDeleteTarget}
                  />
                ))
              ) : (
                !error && (
                  <EmptyState
                    hasSearch={hasSearch}
                    filter={filter}
                    onAdd={() => setModal({ mode: 'create' })}
                  />
                )
              )}
            </div>
          </section>
        </main>

        <footer className="app-footer">Saved locally with SQLite · Lavender</footer>
      </div>

      {modal && (
        <TaskFormModal
          mode={modal.mode}
          task={modal.task}
          onClose={closeModal}
          onSave={handleSave}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          task={deleteTarget}
          busy={deleting}
          onCancel={() => setDeleteTarget(null)}
          onConfirm={handleDelete}
        />
      )}

      {toast && <Toast message={toast.message} tone={toast.tone} />}
    </div>
  );
}
