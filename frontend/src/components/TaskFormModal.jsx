import { useState } from 'react';
import useModalBehavior from '../hooks/useModalBehavior.js';
import { CheckIcon, XIcon } from './Icons.jsx';

const TITLE_MAX = 120;
const DESCRIPTION_MAX = 500;

export default function TaskFormModal({ mode, task, onClose, onSave }) {
  const isEdit = mode === 'edit';
  const [values, setValues] = useState({
    title: task?.title ?? '',
    description: task?.description ?? '',
    due_date: task?.due_date ?? '',
    status: task?.status ?? 'pending',
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  useModalBehavior(onClose, !saving);

  function update(field, value) {
    setValues((current) => ({ ...current, [field]: value }));
    if (errors[field] || errors.form) {
      setErrors((current) => ({ ...current, [field]: undefined, form: undefined }));
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const nextErrors = {};
    const title = values.title.trim();
    const description = values.description.trim();

    if (!title) nextErrors.title = 'Please enter a task title.';
    else if (title.length > TITLE_MAX) nextErrors.title = `Keep the title within ${TITLE_MAX} characters.`;
    if (description.length > DESCRIPTION_MAX) {
      nextErrors.description = `Keep the description within ${DESCRIPTION_MAX} characters.`;
    }

    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      return;
    }

    const payload = {
      title,
      description,
      due_date: values.due_date || null,
    };
    if (isEdit) payload.status = values.status;

    setSaving(true);
    try {
      await onSave(payload);
    } catch (error) {
      setErrors(
        error.fields && Object.keys(error.fields).length
          ? error.fields
          : { form: error.message },
      );
      setSaving(false);
    }
  }

  return (
    <div
      className="modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !saving) onClose();
      }}
    >
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="task-modal-title"
      >
        <div className="modal-head">
          <div>
            <h2 id="task-modal-title">{isEdit ? 'Edit task' : 'New task'}</h2>
            <p>{isEdit ? 'Update the details below.' : 'Add something small to your day.'}</p>
          </div>
          <button
            type="button"
            className="icon-btn modal-close"
            onClick={onClose}
            disabled={saving}
            aria-label="Close dialog"
          >
            <XIcon size={17} />
          </button>
        </div>

        <form className="task-form" onSubmit={handleSubmit} noValidate>
          {errors.form && (
            <p className="form-banner" role="alert">
              {errors.form}
            </p>
          )}

          <label className="field">
            <span className="field-label">
              Title <span className="required">*</span>
            </span>
            <input
              type="text"
              value={values.title}
              onChange={(event) => update('title', event.target.value)}
              maxLength={TITLE_MAX}
              placeholder="What needs to get done?"
              aria-invalid={Boolean(errors.title)}
              autoFocus
            />
            {errors.title && <span className="field-error">{errors.title}</span>}
          </label>

          <label className="field">
            <span className="field-label">Description</span>
            <textarea
              rows={3}
              value={values.description}
              onChange={(event) => update('description', event.target.value)}
              maxLength={DESCRIPTION_MAX}
              placeholder="Add a short note (optional)"
              aria-invalid={Boolean(errors.description)}
            />
            {errors.description && <span className="field-error">{errors.description}</span>}
          </label>

          <div className={isEdit ? 'form-row' : ''}>
            <label className="field">
              <span className="field-label">Due date</span>
              <input
                type="date"
                value={values.due_date}
                onChange={(event) => update('due_date', event.target.value)}
                aria-invalid={Boolean(errors.due_date)}
              />
              {errors.due_date && <span className="field-error">{errors.due_date}</span>}
            </label>

            {isEdit && (
              <div className="field status-field">
                <span className="field-label">Status</span>
                <button
                  type="button"
                  className={`status-toggle ${values.status === 'completed' ? 'is-on' : ''}`}
                  onClick={() =>
                    update('status', values.status === 'completed' ? 'pending' : 'completed')
                  }
                  aria-pressed={values.status === 'completed'}
                >
                  <span className="toggle-box">
                    <CheckIcon size={12} strokeWidth={2.8} />
                  </span>
                  {values.status === 'completed' ? 'Completed' : 'Mark completed'}
                </button>
              </div>
            )}
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving…' : isEdit ? 'Save changes' : 'Add task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
