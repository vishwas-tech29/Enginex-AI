import { FormEvent, useMemo, useState } from 'react';

import { Button } from '@/components/common/Button';
import { useDefaultOrganization } from '@/hooks/useDefaultOrganization';
import { useProject } from '@/hooks/useProject';
import type { ProjectType } from '@/types/models';

interface CreateProjectFormProps {
  onSuccess?: () => void;
}

export function CreateProjectForm({ onSuccess }: CreateProjectFormProps) {
  const { createProject } = useProject();
  const { organizationId, isLoading: isLoadingOrg } = useDefaultOrganization();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<ProjectType>('cad');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isValid = useMemo(() => name.trim().length >= 2, [name]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (!isValid) {
      setError('Project name must be at least 2 characters long.');
      return;
    }
    if (!organizationId) {
      setError('Still setting up your workspace — try again in a moment.');
      return;
    }

    setIsSubmitting(true);
    try {
      await createProject({
        organization_id: organizationId,
        name,
        description,
        type,
      });
      setName('');
      setDescription('');
      setType('cad');
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create project.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">Project name</label>
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2"
          placeholder="Design workspace"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">Description</label>
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          className="min-h-24 w-full rounded-md border border-slate-300 px-3 py-2"
          placeholder="Describe the milestone"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">Type</label>
        <select
          value={type}
          onChange={(event) => setType(event.target.value as ProjectType)}
          className="w-full rounded-md border border-slate-300 px-3 py-2"
        >
          <option value="cad">CAD</option>
          <option value="pcb">PCB</option>
          <option value="mixed">Mixed</option>
          <option value="robotics">Robotics</option>
        </select>
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <Button type="submit" isLoading={isSubmitting} disabled={isLoadingOrg} className="w-full">
        Create project
      </Button>
    </form>
  );
}
