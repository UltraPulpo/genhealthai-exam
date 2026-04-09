import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadDocument } from '../api/orders';

export function useDocumentUpload() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, file }: { orderId: string; file: File }) =>
      uploadDocument(orderId, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
}
