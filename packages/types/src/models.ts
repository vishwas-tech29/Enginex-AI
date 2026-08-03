export type ProjectType = 'cad' | 'pcb' | 'mixed' | 'robotics';
export type ProjectStatus = 'active' | 'archived';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string | null;
}

export interface Project {
  id: string;
  organization_id: string;
  team_id?: string | null;
  name: string;
  description?: string | null;
  owner_id: string;
  type: ProjectType;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}
