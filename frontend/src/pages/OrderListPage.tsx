import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import AddIcon from '@mui/icons-material/Add';
import PageLayout from '../components/common/PageLayout';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import { OrderTable } from '../components/orders';
import { useAuth } from '../hooks/useAuth';
import { useOrders } from '../hooks/useOrders';
import { useDeleteOrder } from '../hooks/useOrders';

export default function OrderListPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const { data, isLoading, isError, error } = useOrders({ page, per_page: 10 });
  const deleteOrder = useDeleteOrder();

  const handleDelete = useCallback(
    async (id: string) => {
      try {
        await deleteOrder.mutateAsync(id);
        setSnackbar({ open: true, message: 'Order deleted successfully.', severity: 'success' });
      } catch {
        setSnackbar({ open: true, message: 'Failed to delete order.', severity: 'error' });
      }
    },
    [deleteOrder],
  );

  const handleRowClick = useCallback(
    (id: string) => navigate(`/orders/${id}`),
    [navigate],
  );

  const handleCloseSnackbar = useCallback(() => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  }, []);

  return (
    <PageLayout title="GenHealth AI" user={user ?? undefined} onLogout={logout}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/orders/new')}
        >
          Create Order
        </Button>
      </Box>

      {isLoading && <LoadingSpinner message="Loading orders..." />}

      {isError && (
        <ErrorAlert
          message={error instanceof Error ? error.message : 'Failed to load orders.'}
        />
      )}

      {data && (
        <OrderTable
          orders={data.data}
          pagination={data.pagination}
          onPageChange={setPage}
          onDelete={handleDelete}
          onRowClick={handleRowClick}
        />
      )}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} variant="filled">
          {snackbar.message}
        </Alert>
      </Snackbar>
    </PageLayout>
  );
}
