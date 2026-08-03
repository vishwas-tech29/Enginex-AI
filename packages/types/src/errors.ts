export interface ApiErrorBody {
  error: {
    message: string;
    status_code?: number;
    details?: unknown;
  };
}
