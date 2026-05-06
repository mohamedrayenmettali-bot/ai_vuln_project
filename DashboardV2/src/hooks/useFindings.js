import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { findingsApi } from '../api/findings.api';

export function useFindings(projectId, params) {
  return useQuery({
    queryKey: ['findings', projectId, params],
    queryFn: () => findingsApi.getAll(projectId, params).then((r) => r.data),
    enabled: !!projectId,
    staleTime: 30_000,
    keepPreviousData: true,
  });
}

export function useFinding(id) {
  return useQuery({
    queryKey: ['finding', id],
    queryFn: () => findingsApi.getById(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useUpdateFindingStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }) => findingsApi.updateStatus(id, status),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ['finding', id] });
      qc.invalidateQueries({ queryKey: ['findings'] });
    },
  });
}

export function useSubmitFeedback() {
  return useMutation({
    mutationFn: ({ id, data }) => findingsApi.submitFeedback(id, data),
  });
}

export function useFindingHistory(id) {
  return useQuery({
    queryKey: ['finding-history', id],
    queryFn: () => findingsApi.getHistory(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useFindingAiAnalysis(id) {
  return useQuery({
    queryKey: ['finding-ai', id],
    queryFn: () => findingsApi.getAiAnalysis(id).then((r) => r.data),
    enabled: !!id,
  });
}
