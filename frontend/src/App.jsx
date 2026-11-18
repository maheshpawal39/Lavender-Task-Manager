import { useEffect, useState } from 'react';
import { authApi } from './api.js';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';
import { CheckIcon } from './components/Icons.jsx';

export default function App() {
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [authView, setAuthView] = useState('login');

  useEffect(() => {
    let active = true;

    function handleExpired() {
      setUser(null);
      setAuthView('login');
    }

    authApi
      .me()
      .then((data) => {
        if (active) setUser(data.user);
      })
      .catch(() => {
        // No active session: the login page is shown below.
      })
      .finally(() => {
        if (active) setCheckingSession(false);
      });

    window.addEventListener('auth:expired', handleExpired);
    return () => {
      active = false;
      window.removeEventListener('auth:expired', handleExpired);
    };
  }, []);

  async function handleLogout() {
    try {
      await authApi.logout();
    } catch {
      // Clear the local session even if the network request fails.
    }
    setUser(null);
    setAuthView('login');
  }

  if (checkingSession) {
    return (
      <div className="boot-screen">
        <span className="brand-mark">
          <CheckIcon size={17} strokeWidth={2.6} />
        </span>
        <span className="spinner" aria-hidden="true" />
        <span className="sr-only">Loading</span>
      </div>
    );
  }

  if (!user) {
    return authView === 'register' ? (
      <Register onAuthenticated={setUser} onSwitch={() => setAuthView('login')} />
    ) : (
      <Login onAuthenticated={setUser} onSwitch={() => setAuthView('register')} />
    );
  }

  return <Dashboard user={user} onLogout={handleLogout} />;
}
