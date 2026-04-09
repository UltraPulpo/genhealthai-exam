import Alert from '@mui/material/Alert';

interface ErrorAlertProps {
  message: string;
  onClose?: () => void;
}

export default function ErrorAlert({ message, onClose }: ErrorAlertProps) {
  return (
    <Alert severity="error" onClose={onClose}>
      {message}
    </Alert>
  );
}
