import { type FormEvent, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import CircularProgress from '@mui/material/CircularProgress';
import type { Order } from '../../types';
import { validateRequired, validateNPI } from '../../utils/validators';

interface OrderFormProps {
  initialValues?: Partial<Order>;
  onSubmit: (data: Partial<Order>) => void;
  isLoading?: boolean;
}

interface FormState {
  patient_first_name: string;
  patient_last_name: string;
  patient_dob: string;
  insurance_provider: string;
  insurance_id: string;
  group_number: string;
  ordering_provider_name: string;
  provider_npi: string;
  provider_phone: string;
  equipment_type: string;
  equipment_description: string;
  hcpcs_code: string;
  authorization_number: string;
  authorization_status: string;
  delivery_address: string;
  delivery_date: string;
  delivery_notes: string;
}

type FormErrors = Partial<Record<keyof FormState, string | null>>;

function initFormState(values?: Partial<Order>): FormState {
  return {
    patient_first_name: values?.patient_first_name ?? '',
    patient_last_name: values?.patient_last_name ?? '',
    patient_dob: values?.patient_dob ?? '',
    insurance_provider: values?.insurance_provider ?? '',
    insurance_id: values?.insurance_id ?? '',
    group_number: values?.group_number ?? '',
    ordering_provider_name: values?.ordering_provider_name ?? '',
    provider_npi: values?.provider_npi ?? '',
    provider_phone: values?.provider_phone ?? '',
    equipment_type: values?.equipment_type ?? '',
    equipment_description: values?.equipment_description ?? '',
    hcpcs_code: values?.hcpcs_code ?? '',
    authorization_number: values?.authorization_number ?? '',
    authorization_status: values?.authorization_status ?? '',
    delivery_address: values?.delivery_address ?? '',
    delivery_date: values?.delivery_date ?? '',
    delivery_notes: values?.delivery_notes ?? '',
  };
}

function validateForm(state: FormState): FormErrors {
  const errors: FormErrors = {};
  errors.patient_first_name = validateRequired(state.patient_first_name, 'First name');
  errors.patient_last_name = validateRequired(state.patient_last_name, 'Last name');
  errors.equipment_type = validateRequired(state.equipment_type, 'Equipment type');
  if (state.provider_npi) {
    errors.provider_npi = validateNPI(state.provider_npi);
  }
  return errors;
}

function hasErrors(errors: FormErrors): boolean {
  return Object.values(errors).some((v) => v != null);
}

export default function OrderForm({ initialValues, onSubmit, isLoading }: OrderFormProps) {
  const [form, setForm] = useState<FormState>(() => initFormState(initialValues));
  const [errors, setErrors] = useState<FormErrors>({});

  const handleChange = (field: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setErrors((prev) => ({ ...prev, [field]: null }));
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const validationErrors = validateForm(form);
    setErrors(validationErrors);
    if (hasErrors(validationErrors)) return;

    const data: Partial<Order> = {};
    for (const [key, value] of Object.entries(form)) {
      if (value) {
        (data as Record<string, string>)[key] = value;
      }
    }
    onSubmit(data);
  };

  const field = (name: keyof FormState, label: string, opts?: { type?: string; multiline?: boolean }) => (
    <Grid size={{ xs: 12, sm: 6 }}>
      <TextField
        fullWidth
        label={label}
        value={form[name]}
        onChange={handleChange(name)}
        error={!!errors[name]}
        helperText={errors[name] ?? ''}
        type={opts?.type ?? 'text'}
        multiline={opts?.multiline}
        rows={opts?.multiline ? 3 : undefined}
        slotProps={opts?.type === 'date' ? { inputLabel: { shrink: true } } : undefined}
      />
    </Grid>
  );

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      <Typography variant="h6" gutterBottom>Patient Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {field('patient_first_name', 'First Name')}
        {field('patient_last_name', 'Last Name')}
        {field('patient_dob', 'Date of Birth', { type: 'date' })}
      </Grid>

      <Typography variant="h6" gutterBottom>Insurance Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {field('insurance_provider', 'Insurance Provider')}
        {field('insurance_id', 'Insurance ID')}
        {field('group_number', 'Group Number')}
      </Grid>

      <Typography variant="h6" gutterBottom>Provider Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {field('ordering_provider_name', 'Provider Name')}
        {field('provider_npi', 'NPI')}
        {field('provider_phone', 'Phone')}
      </Grid>

      <Typography variant="h6" gutterBottom>Equipment Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {field('equipment_type', 'Equipment Type')}
        {field('equipment_description', 'Description', { multiline: true })}
        {field('hcpcs_code', 'HCPCS Code')}
      </Grid>

      <Typography variant="h6" gutterBottom>Authorization</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {field('authorization_number', 'Authorization Number')}
        {field('authorization_status', 'Authorization Status')}
      </Grid>

      <Typography variant="h6" gutterBottom>Delivery Information</Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {field('delivery_address', 'Delivery Address', { multiline: true })}
        {field('delivery_date', 'Delivery Date', { type: 'date' })}
        {field('delivery_notes', 'Delivery Notes', { multiline: true })}
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
        <Button
          type="submit"
          variant="contained"
          disabled={isLoading}
          startIcon={isLoading ? <CircularProgress size={20} /> : undefined}
        >
          {initialValues ? 'Update Order' : 'Create Order'}
        </Button>
      </Box>
    </Box>
  );
}
