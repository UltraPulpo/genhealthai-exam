import { useState, useCallback } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Link as MuiLink,
  Paper,
} from '@mui/material';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';
import { validateEmail, validatePassword, validateRequired } from '../../utils/validators';
import type { ApiError } from '../../types';

function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as ApiError | undefined;
    return data?.error?.message ?? err.message;
  }
  if (err instanceof Error) return err.message;
  return 'An unexpected error occurred';
}

export default function RegisterForm() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [firstNameError, setFirstNameError] = useState<string | null>(null);
  const [lastNameError, setLastNameError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();

      const emailErr = validateEmail(email);
      const passwordErr = validatePassword(password);
      const firstNameErr = validateRequired(firstName, 'First Name');
      const lastNameErr = validateRequired(lastName, 'Last Name');
      setEmailError(emailErr);
      setPasswordError(passwordErr);
      setFirstNameError(firstNameErr);
      setLastNameError(lastNameErr);
      if (emailErr || passwordErr || firstNameErr || lastNameErr) return;

      setApiError(null);
      setIsSubmitting(true);
      try {
        await register({ email, password, first_name: firstName, last_name: lastName });
        navigate('/login');
      } catch (err: unknown) {
        setApiError(extractErrorMessage(err));
      } finally {
        setIsSubmitting(false);
      }
    },
    [email, password, firstName, lastName, register, navigate],
  );

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
      }}
    >
      <Paper elevation={3} sx={{ p: 4, width: '100%', maxWidth: 400 }}>
        <Typography variant="h5" component="h1" gutterBottom textAlign="center">
          Create Account
        </Typography>

        {apiError && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setApiError(null)}>
            {apiError}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            label="First Name"
            fullWidth
            margin="normal"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            error={Boolean(firstNameError)}
            helperText={firstNameError}
            disabled={isSubmitting}
            autoComplete="given-name"
          />
          <TextField
            label="Last Name"
            fullWidth
            margin="normal"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            error={Boolean(lastNameError)}
            helperText={lastNameError}
            disabled={isSubmitting}
            autoComplete="family-name"
          />
          <TextField
            label="Email"
            type="email"
            fullWidth
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={Boolean(emailError)}
            helperText={emailError}
            disabled={isSubmitting}
            autoComplete="email"
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={Boolean(passwordError)}
            helperText={passwordError}
            disabled={isSubmitting}
            autoComplete="new-password"
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 2 }}
            disabled={isSubmitting}
          >
            {isSubmitting ? <CircularProgress size={24} color="inherit" /> : 'Create Account'}
          </Button>
        </Box>

        <Typography variant="body2" textAlign="center" sx={{ mt: 2 }}>
          Already have an account?{' '}
          <MuiLink component={Link} to="/login" underline="hover">
            Sign in
          </MuiLink>
        </Typography>
      </Paper>
    </Box>
  );
}
