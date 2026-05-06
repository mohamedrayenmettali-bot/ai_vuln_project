import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { projectsApi } from '../api/projects.api';

export function useProjects(params) {
  return useQuery({
    queryKey: ['projects', params],
    queryFn: () => projectsApi.getAll(params).then((r) => r.data),
    staleTime: 60_000,
  });
}

export function useProject(id) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.getById(id).then((r) => r.data),
    enabled: !!id,
    staleTime: 60_000,
  });
}

export function useProjectOverview(id) {
  return useQuery({
    queryKey: ['project-overview', id],
    queryFn: () => projectsApi.getOverview(id).then((r) => r.data),
    enabled: !!id,
    staleTime: 30_000,
  });
}

export function useProjectPipeline(id) {
  return useQuery({
    queryKey: ['project-pipeline', id],
    queryFn: () => projectsApi.getPipeline(id).then((r) => r.data),
    enabled: !!id,
    staleTime: 30_000,
  });
}

export function useRunScan(id) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => projectsApi.runScan(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project', id] });
      qc.invalidateQueries({ queryKey: ['project-pipeline', id] });
    },
  });
}

export function useSyncFindings(id) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => projectsApi.syncFindings(id),
    onSuccess: (response) => {
      qc.invalidateQueries({ queryKey: ['project', id] });
      qc.invalidateQueries({ queryKey: ['project-overview', id] });
      qc.invalidateQueries({ queryKey: ['project-findings', id] });
      const conflicts = response.data.conflicts || 0;
      const conflictText = conflicts ? ` (${conflicts} conflict${conflicts === 1 ? '' : 's'} preserved)` : '';
      toast.success(`Successfully synced ${response.data.total_imported} findings from DefectDojo${conflictText}!`);
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || 'Failed to sync findings from DefectDojo.');
    },
  });
}
