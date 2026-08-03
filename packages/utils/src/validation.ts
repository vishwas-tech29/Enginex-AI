const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function isValidEmail(email: string): boolean {
  return EMAIL_RE.test(email);
}

export function isValidPassword(password: string): boolean {
  return password.length >= 8 && /[A-Za-z]/.test(password) && /\d/.test(password);
}
