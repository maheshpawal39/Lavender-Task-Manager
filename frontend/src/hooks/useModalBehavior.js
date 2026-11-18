import { useEffect } from 'react';

const FOCUSABLE =
  'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])';

/** Close on Escape, trap focus inside the dialog, and lock background scrolling. */
export default function useModalBehavior(onClose, enabled = true) {
  useEffect(() => {
    const dialog = document.querySelector('.modal');

    function handleKeyDown(event) {
      if (event.key === 'Escape' && enabled) {
        onClose();
        return;
      }

      if (event.key !== 'Tab' || !dialog) return;

      const focusable = [...dialog.querySelectorAll(FOCUSABLE)].filter(
        (element) => element.offsetParent !== null,
      );
      if (!focusable.length) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose, enabled]);
}
