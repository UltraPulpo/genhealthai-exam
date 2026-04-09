import { describe, it, expect } from 'vitest';
import { validateEmail, validatePassword, validateRequired, validateNPI } from '../validators';

describe('validateEmail', () => {
  it('returns null for a valid email', () => {
    expect(validateEmail('user@example.com')).toBeNull();
  });

  it('returns null for email with subdomain', () => {
    expect(validateEmail('user@mail.example.com')).toBeNull();
  });

  it('returns null for email with plus addressing', () => {
    expect(validateEmail('user+tag@example.com')).toBeNull();
  });

  it('returns error for empty string', () => {
    expect(validateEmail('')).toBe('Valid email is required');
  });

  it('returns error for missing @', () => {
    expect(validateEmail('userexample.com')).toBe('Valid email is required');
  });

  it('returns error for missing domain', () => {
    expect(validateEmail('user@')).toBe('Valid email is required');
  });

  it('returns error for missing local part', () => {
    expect(validateEmail('@example.com')).toBe('Valid email is required');
  });

  it('returns error for spaces', () => {
    expect(validateEmail('user @example.com')).toBe('Valid email is required');
  });
});

describe('validatePassword', () => {
  it('returns null for a valid password', () => {
    expect(validatePassword('Abcdefg1')).toBeNull();
  });

  it('returns null for a strong password', () => {
    expect(validatePassword('MyP@ssw0rd!')).toBeNull();
  });

  it('returns error when too short', () => {
    const result = validatePassword('Ab1');
    expect(result).toContain('at least 8 characters');
  });

  it('returns error when missing uppercase', () => {
    const result = validatePassword('abcdefg1');
    expect(result).toContain('uppercase');
  });

  it('returns error when missing lowercase', () => {
    const result = validatePassword('ABCDEFG1');
    expect(result).toContain('lowercase');
  });

  it('returns error when missing digit', () => {
    const result = validatePassword('Abcdefgh');
    expect(result).toContain('digit');
  });

  it('returns error for empty string', () => {
    const result = validatePassword('');
    expect(result).not.toBeNull();
  });
});

describe('validateRequired', () => {
  it('returns null for non-empty string', () => {
    expect(validateRequired('hello', 'Name')).toBeNull();
  });

  it('returns error for empty string', () => {
    expect(validateRequired('', 'Name')).toBe('Name is required');
  });

  it('returns error for whitespace-only string', () => {
    expect(validateRequired('   ', 'Email')).toBe('Email is required');
  });

  it('includes field name in error message', () => {
    expect(validateRequired('', 'Patient ID')).toBe('Patient ID is required');
  });
});

describe('validateNPI', () => {
  it('returns null for a valid 10-digit NPI', () => {
    expect(validateNPI('1234567890')).toBeNull();
  });

  it('returns error for fewer than 10 digits', () => {
    expect(validateNPI('123456789')).toContain('10-digit');
  });

  it('returns error for more than 10 digits', () => {
    expect(validateNPI('12345678901')).toContain('10-digit');
  });

  it('returns error for non-numeric characters', () => {
    expect(validateNPI('12345abcde')).toContain('10-digit');
  });

  it('returns error for empty string', () => {
    expect(validateNPI('')).toContain('10-digit');
  });

  it('returns error for NPI with spaces', () => {
    expect(validateNPI('123 456 789')).toContain('10-digit');
  });
});
