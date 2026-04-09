import { useState } from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Tooltip from '@mui/material/Tooltip';
import DeleteIcon from '@mui/icons-material/Delete';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import type { Order, Pagination } from '../../types';
import ConfirmDialog from '../common/ConfirmDialog';
import OrderStatusChip from './OrderStatusChip';

interface OrderTableProps {
  orders: Order[];
  pagination: Pagination;
  onPageChange: (page: number) => void;
  onDelete: (id: string) => void;
  onRowClick: (id: string) => void;
}

export default function OrderTable({
  orders,
  pagination,
  onPageChange,
  onDelete,
  onRowClick,
}: OrderTableProps) {
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const handleConfirmDelete = () => {
    if (deleteTarget) {
      onDelete(deleteTarget);
      setDeleteTarget(null);
    }
  };

  return (
    <Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Order ID</TableCell>
              <TableCell>Patient Name</TableCell>
              <TableCell>DOB</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Equipment Type</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {orders.map((order) => (
              <TableRow
                key={order.id}
                hover
                sx={{ cursor: 'pointer' }}
                onClick={() => onRowClick(order.id)}
              >
                <TableCell>{order.id.substring(0, 8)}</TableCell>
                <TableCell>
                  {[order.patient_first_name, order.patient_last_name]
                    .filter(Boolean)
                    .join(' ') || '—'}
                </TableCell>
                <TableCell>{order.patient_dob ?? '—'}</TableCell>
                <TableCell>
                  <OrderStatusChip status={order.status} />
                </TableCell>
                <TableCell>{order.equipment_type ?? '—'}</TableCell>
                <TableCell>
                  {new Date(order.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell align="right">
                  <Box
                    onClick={(e) => e.stopPropagation()}
                    sx={{ display: 'inline-flex', gap: 0.5 }}
                  >
                    {(order.status === 'pending' || order.status === 'failed') && !order.document && (
                      <Tooltip title="Upload Document">
                        <IconButton
                          size="small"
                          onClick={() => onRowClick(order.id)}
                          aria-label="upload document"
                        >
                          <UploadFileIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Delete Order">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => setDeleteTarget(order.id)}
                        aria-label="delete order"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
            {orders.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No orders found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={pagination.total}
        page={pagination.page - 1}
        onPageChange={(_e, newPage) => onPageChange(newPage + 1)}
        rowsPerPage={pagination.per_page}
        rowsPerPageOptions={[pagination.per_page]}
      />

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete Order"
        message="Are you sure you want to delete this order? This action cannot be undone."
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </Box>
  );
}
