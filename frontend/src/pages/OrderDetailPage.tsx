import { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PageLayout from '../components/common/PageLayout';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';
import ConfirmDialog from '../components/common/ConfirmDialog';
import { OrderDetail, OrderForm, DocumentUpload } from '../components/orders';
import { useAuth } from '../hooks/useAuth';
import { useOrder, useUpdateOrder, useDeleteOrder } from '../hooks/useOrders';
import type { Order } from '../types';

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const { data: order, isLoading, isError, error } = useOrder(id!);
  const updateOrder = useUpdateOrder();
  const deleteOrder = useDeleteOrder();

  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const handleUpdate = useCallback(
    async (data: Partial<Order>) => {
      try {
        await updateOrder.mutateAsync({ id: id!, data });
        setIsEditing(false);
        setSnackbar({ open: true, message: 'Order updated successfully.', severity: 'success' });
      } catch {
        setSnackbar({ open: true, message: 'Failed to update order.', severity: 'error' });
      }
    },
    [id, updateOrder],
  );

  const handleDelete = useCallback(async () => {
    try {
      await deleteOrder.mutateAsync(id!);
      navigate('/orders');
    } catch {
      setSnackbar({ open: true, message: 'Failed to delete order.', severity: 'error' });
      setShowDeleteDialog(false);
    }
  }, [id, deleteOrder, navigate]);

  const handleCloseSnackbar = useCallback(() => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  }, []);

  return (
    <PageLayout title="GenHealth AI" user={user ?? undefined} onLogout={logout}>
      <Box sx={{ mb: 2 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/orders')}>
          Back to Orders
        </Button>
      </Box>

      {isLoading && <LoadingSpinner message="Loading order..." />}

      {isError && (
        <ErrorAlert
          message={error instanceof Error ? error.message : 'Failed to load order.'}
        />
      )}

      {order && !isEditing && (
        <>
          <OrderDetail
            order={order}
            onEdit={() => setIsEditing(true)}
            onDelete={() => setShowDeleteDialog(true)}
          />
          {!order.document && (
            <Box sx={{ mt: 3 }}>
              <DocumentUpload orderId={order.id} />
            </Box>
          )}
        </>
      )}

      {order && isEditing && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box />
            <Button variant="outlined" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
          </Box>
          <OrderForm
            initialValues={order}
            onSubmit={handleUpdate}
            isLoading={updateOrder.isPending}
          />
        </Box>
      )}

      <ConfirmDialog
        open={showDeleteDialog}
        title="Delete Order"
        message="Are you sure you want to delete this order? This action cannot be undone."
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteDialog(false)}
      />

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
