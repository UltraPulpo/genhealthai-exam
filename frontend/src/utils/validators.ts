const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const NPI_REGEX = /^\d{10}$/;

export function validateEmail(email: string): string | null {
  if (!EMAIL_REGEX.test(email)) {
    return 'Valid email is required';
  }
  return null;
}

export function validatePassword(password: string): string | null {
  const issues: string[] = [];

  if (password.length < 8) {
    issues.push('at least 8 characters');
  }
  if (!/[A-Z]/.test(password)) {
    issues.push('uppercase letter');
  }
  if (!/[a-z]/.test(password)) {
    issues.push('lowercase letter');
  }
  if (!/\d/.test(password)) {
    issues.push('digit');
  }

  if (issues.length > 0) {
    return `Password must contain: ${issues.join(', ')}`;
  }
  return null;
}

export function validateRequired(value: string, fieldName: string): string | null {
  if (!value.trim()) {
    return `${fieldName} is required`;
  }
  return null;
}

export function validateNPI(npi: string): string | null {
  if (!NPI_REGEX.test(npi)) {
    return 'NPI must be a 10-digit number';
  }
  return null;
}
