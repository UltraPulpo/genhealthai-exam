import Chip from '@mui/material/Chip';
import type { OrderStatus } from '../../types';

interface OrderStatusChipProps {
  status: OrderStatus;
}

const statusConfig: Record<OrderStatus, { label: string; color: 'default' | 'info' | 'success' | 'error' }> = {
  pending: { label: 'Pending', color: 'default' },
  processing: { label: 'Processing', color: 'info' },
  completed: { label: 'Completed', color: 'success' },
  failed: { label: 'Failed', color: 'error' },
};

export default function OrderStatusChip({ status }: OrderStatusChipProps) {
  const config = statusConfig[status];
  return <Chip label={config.label} color={config.color} size="small" />;
}
