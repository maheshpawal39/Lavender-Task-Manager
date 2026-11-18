import { CheckCircleIcon, XIcon } from './Icons.jsx';

export default function Toast({ message, tone = 'success' }) {
  return (
    <div className={`toast ${tone}`} role="status" aria-live="polite">
      {tone === 'error' ? <XIcon size={15} /> : <CheckCircleIcon size={15} />}
      <span>{message}</span>
    </div>
  );
}
