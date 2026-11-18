import { useState } from 'react';
import { authApi } from '../api.js';
import AuthShell from '../components/AuthShell.jsx';
import PasswordInput from '../components/PasswordInput.jsx';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PASSWORD_MIN = 8;

export default function Register({ onAuthenticated, onSwitch }) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const setters = {
    full_name: setFullName,
    email: setEmail,
    password: setPassword,
    confirm_password: setConfirmPassword,
  };

  function update(field, value) {
    setters[field](value);
    if (errors[field] || errors.form) {
      setErrors((current) => ({ ...current, [field]: undefined, form: undefined }));
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const nextErrors = {};
    if (!fullName.trim()) nextErrors.full_name = 'Please enter your full name.';
    else if (fullName.trim().length > 80) nextErrors.full_name = 'Name must be 80 characters or fewer.';

    if (!email.trim()) nextErrors.email = 'Email address is required.';
    else if (!EMAIL_RE.test(email.trim())) nextErrors.email = 'Please enter a valid email address.';

    if (!password) nextErrors.password = 'Password is required.';
    else if (password.length < PASSWORD_MIN) {
      nextErrors.password = `Password must be at least ${PASSWORD_MIN} characters.`;
    }

    if (!confirmPassword) nextErrors.confirm_password = 'Please confirm your password.';
    else if (confirmPassword !== password) {
      nextErrors.confirm_password = 'Passwords do not match.';
    }

    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      return;
    }

    setSubmitting(true);
    try {
      const data = await authApi.register({
        fullName: fullName.trim(),
        email: email.trim(),
        password,
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
        <h2>Create your account</h2>
        <p>A quiet space for your tasks and plans.</p>
      </div>

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {errors.form && (
          <p className="form-banner" role="alert">
            {errors.form}
          </p>
        )}

        <div className="field">
          <label className="field-label" htmlFor="register-name">
            Full name
          </label>
          <input
            id="register-name"
            type="text"
            value={fullName}
            onChange={(event) => update('full_name', event.target.value)}
            placeholder="Your name"
            autoComplete="name"
            maxLength={80}
            aria-invalid={Boolean(errors.full_name)}
            autoFocus
            required
          />
          {errors.full_name && <span className="field-error">{errors.full_name}</span>}
        </div>

        <div className="field">
          <label className="field-label" htmlFor="register-email">
            Email address
          </label>
          <input
            id="register-email"
            type="email"
            value={email}
            onChange={(event) => update('email', event.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            autoCapitalize="none"
            spellCheck={false}
            aria-invalid={Boolean(errors.email)}
            required
          />
          {errors.email && <span className="field-error">{errors.email}</span>}
        </div>

        <div className="field">
          <label className="field-label" htmlFor="register-password">
            Password
          </label>
          <PasswordInput
            id="register-password"
            value={password}
            onChange={(value) => update('password', value)}
            placeholder="At least 8 characters"
            autoComplete="new-password"
            invalid={Boolean(errors.password)}
          />
          {errors.password ? (
            <span className="field-error">{errors.password}</span>
          ) : (
            <span className="field-hint">Use at least {PASSWORD_MIN} characters.</span>
          )}
        </div>

        <div className="field">
          <label className="field-label" htmlFor="register-confirm">
            Confirm password
          </label>
          <PasswordInput
            id="register-confirm"
            value={confirmPassword}
            onChange={(value) => update('confirm_password', value)}
            placeholder="Repeat your password"
            autoComplete="new-password"
            invalid={Boolean(errors.confirm_password)}
          />
          {errors.confirm_password && (
            <span className="field-error">{errors.confirm_password}</span>
          )}
        </div>

        <button type="submit" className="btn btn-primary auth-submit" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>

      <p className="auth-switch">
        Already have an account?{' '}
        <button type="button" className="link-btn" onClick={onSwitch}>
          Sign in
        </button>
      </p>
    </AuthShell>
  );
}
