import { Navigate } from 'react-router-dom';
import { LoginForm } from '../components/auth';
import { useAuth } from '../hooks/useAuth';

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return null;
  if (isAuthenticated) return <Navigate to="/orders" replace />;

  return <LoginForm />;
}
