import { useState } from 'react';
import { authApi } from '../api.js';
import AuthShell from '../components/AuthShell.jsx';
import PasswordInput from '../components/PasswordInput.jsx';
import { CheckIcon } from '../components/Icons.jsx';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Login({ onAuthenticated, onSwitch }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  function update(field, value) {
    if (field === 'email') setEmail(value);
    else setPassword(value);
    if (errors[field] || errors.form) {
      setErrors((current) => ({ ...current, [field]: undefined, form: undefined }));
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const nextErrors = {};
    if (!email.trim()) nextErrors.email = 'Email address is required.';
    else if (!EMAIL_RE.test(email.trim())) nextErrors.email = 'Please enter a valid email address.';
    if (!password) nextErrors.password = 'Password is required.';

    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      return;
    }

    setSubmitting(true);
    try {
      const data = await authApi.login({
        email: email.trim(),
        password,
        rememberMe: remember,
      });
      onAuthenticated(data.user);
    } catch (error) {
      setErrors(
        error.fields && Object.keys(error.fields).length
          ? error.fields
          : { form: error.message },
      );
      setSubmitting(false);
    }
  }

  return (
    <AuthShell>
      <div className="auth-heading">
        <h2>Welcome back</h2>
        <p>Sign in to continue to your tasks.</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {errors.form && (
          <p className="form-banner" role="alert">
            {errors.form}
          </p>
        )}

        <div className="field">
          <label className="field-label" htmlFor="login-email">
            Email address
          </label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(event) => update('email', event.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            autoCapitalize="none"
            spellCheck={false}
            aria-invalid={Boolean(errors.email)}
            autoFocus
            required
          />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </div>

        <div className="field">
          <label className="field-label" htmlFor="login-password">
            Password
          </label>
          <PasswordInput
            id="login-password"
            value={password}
            onChange={(value) => update('password', value)}
            placeholder="Enter your password"
            autoComplete="current-password"
            invalid={Boolean(errors.password)}
          />
          {errors.password && <span className="field-error">{errors.password}</span>}
        </div>

        <div className="auth-options">
          <label className="remember-row">
            <input
              type="checkbox"
              checked={remember}
              onChange={(event) => setRemember(event.target.checked)}
            />
            <span className="checkbox-box">
              <CheckIcon size={10} strokeWidth={3} />
            </span>
            Remember me
          </label>
        </div>

        <button type="submit" className="btn btn-primary auth-submit" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <p className="auth-switch">
        New here?{' '}
        <button type="button" className="link-btn" onClick={onSwitch}>
          Create an account
        </button>
      </p>
    </AuthShell>
  );
}
