import { type ChangeEvent, useRef, useState } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import LoadingSpinner from '../common/LoadingSpinner';
import { useDocumentUpload } from '../../hooks/useDocumentUpload';

interface DocumentUploadProps {
  orderId: string;
}

export default function DocumentUpload({ orderId }: DocumentUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const mutation = useDocumentUpload();

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      mutation.reset();
    }
  };

  const handleUpload = () => {
    if (!selectedFile) return;
    mutation.mutate({ orderId, file: selectedFile });
  };

  if (mutation.isPending) {
    return <LoadingSpinner message="Uploading document..." />;
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Upload Document
      </Typography>

      {mutation.isSuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Document uploaded successfully.
        </Alert>
      )}

      {mutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {mutation.error instanceof Error
            ? mutation.error.message
            : 'Failed to upload document.'}
        </Alert>
      )}

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <Button
          variant="outlined"
          startIcon={<UploadFileIcon />}
          onClick={() => fileInputRef.current?.click()}
        >
          Select PDF
        </Button>
        {selectedFile && (
          <Typography variant="body2" color="text.secondary">
            {selectedFile.name}
          </Typography>
        )}
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!selectedFile}
        >
          Upload
        </Button>
      </Box>
    </Box>
  );
}
