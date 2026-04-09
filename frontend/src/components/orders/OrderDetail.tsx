import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import type { Order } from '../../types';
import OrderStatusChip from './OrderStatusChip';

interface OrderDetailProps {
  order: Order;
  onEdit: () => void;
  onDelete: () => void;
}

function DetailField({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <Grid size={{ xs: 12, sm: 6 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body1">{value || '—'}</Typography>
    </Grid>
  );
}

export default function OrderDetail({ order, onEdit, onDelete }: OrderDetailProps) {
  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Order {order.id.substring(0, 8)}
          </Typography>
          <OrderStatusChip status={order.status} />
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<EditIcon />} onClick={onEdit}>
            Edit
          </Button>
          <Button variant="outlined" color="error" startIcon={<DeleteIcon />} onClick={onDelete}>
            Delete
          </Button>
        </Box>
      </Box>

      {order.error_message && (
        <Typography color="error" sx={{ mb: 2 }}>
          Error: {order.error_message}
        </Typography>
      )}

      <Divider sx={{ my: 2 }} />
      <Typography variant="h6" gutterBottom>Patient Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <DetailField label="First Name" value={order.patient_first_name} />
        <DetailField label="Last Name" value={order.patient_last_name} />
        <DetailField label="Date of Birth" value={order.patient_dob} />
      </Grid>

      <Divider sx={{ my: 2 }} />
      <Typography variant="h6" gutterBottom>Insurance Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <DetailField label="Provider" value={order.insurance_provider} />
        <DetailField label="Insurance ID" value={order.insurance_id} />
        <DetailField label="Group Number" value={order.group_number} />
      </Grid>

      <Divider sx={{ my: 2 }} />
      <Typography variant="h6" gutterBottom>Provider Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <DetailField label="Provider Name" value={order.ordering_provider_name} />
        <DetailField label="NPI" value={order.provider_npi} />
        <DetailField label="Phone" value={order.provider_phone} />
      </Grid>

      <Divider sx={{ my: 2 }} />
      <Typography variant="h6" gutterBottom>Equipment Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <DetailField label="Equipment Type" value={order.equipment_type} />
        <DetailField label="Description" value={order.equipment_description} />
        <DetailField label="HCPCS Code" value={order.hcpcs_code} />
      </Grid>

      <Divider sx={{ my: 2 }} />
      <Typography variant="h6" gutterBottom>Authorization</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <DetailField label="Authorization Number" value={order.authorization_number} />
        <DetailField label="Authorization Status" value={order.authorization_status} />
      </Grid>

      <Divider sx={{ my: 2 }} />
      <Typography variant="h6" gutterBottom>Delivery Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <DetailField label="Address" value={order.delivery_address} />
        <DetailField label="Delivery Date" value={order.delivery_date} />
        <DetailField label="Notes" value={order.delivery_notes} />
      </Grid>

      {order.document && (
        <>
          <Divider sx={{ my: 2 }} />
          <Typography variant="h6" gutterBottom>Document</Typography>
          <Grid container spacing={2}>
            <DetailField label="Filename" value={order.document.original_filename} />
            <DetailField label="Content Type" value={order.document.content_type} />
            <DetailField
              label="File Size"
              value={`${(order.document.file_size_bytes / 1024).toFixed(1)} KB`}
            />
            <DetailField label="Uploaded At" value={new Date(order.document.uploaded_at).toLocaleString()} />
          </Grid>
        </>
      )}

      <Divider sx={{ my: 2 }} />
      <Grid container spacing={2}>
        <DetailField label="Created At" value={new Date(order.created_at).toLocaleString()} />
        <DetailField label="Updated At" value={new Date(order.updated_at).toLocaleString()} />
      </Grid>
    </Paper>
  );
}
