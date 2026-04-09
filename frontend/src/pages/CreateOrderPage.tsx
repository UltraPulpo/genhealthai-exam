import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PageLayout from '../components/common/PageLayout';
import { OrderForm } from '../components/orders';
import { useAuth } from '../hooks/useAuth';
import { useCreateOrder } from '../hooks/useOrders';
import type { Order } from '../types';

export default function CreateOrderPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const createOrder = useCreateOrder();

  const handleSubmit = useCallback(
    async (data: Partial<Order>) => {
      const result = await createOrder.mutateAsync(data);
      navigate(`/orders/${result.id}`);
    },
    [createOrder, navigate],
  );

  return (
    <PageLayout title="GenHealth AI" user={user ?? undefined} onLogout={logout}>
      <Box sx={{ mb: 2 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/orders')}>
          Back to Orders
        </Button>
      </Box>
      <OrderForm onSubmit={handleSubmit} isLoading={createOrder.isPending} />
    </PageLayout>
  );
}
