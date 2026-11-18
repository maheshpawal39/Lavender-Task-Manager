export function dueDateInfo(dueDate, status) {
  if (!dueDate) return null;

  const [year, month, day] = dueDate.split('-').map(Number);
  const due = new Date(year, month - 1, day);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  due.setHours(0, 0, 0, 0);

  const diffDays = Math.round((due - today) / 86_400_000);
  const overdue = diffDays < 0 && status !== 'completed';
  const sameYear = due.getFullYear() === today.getFullYear();
  const formatted = due.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    ...(sameYear ? {} : { year: 'numeric' }),
  });

  let label;
  if (diffDays === 0) label = 'Today';
  else if (diffDays === 1) label = 'Tomorrow';
  else if (diffDays === -1) label = 'Yesterday';
  else label = formatted;

  return {
    label: overdue ? `Overdue · ${formatted}` : label,
    overdue,
    title: due.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    }),
  };
}

export function isDueToday(dueDate) {
  return dueDate === todayISO();
}
