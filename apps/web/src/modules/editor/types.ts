export interface PresenceEntry {
  user_id: string;
  name: string;
  cursor: { x: number; y: number } | null;
  selection: unknown;
}
