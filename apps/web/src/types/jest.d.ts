declare const describe: (name: string, fn: () => void) => void;
declare const it: (name: string, fn: () => void | Promise<void>) => void;
declare const expect: unknown;
declare const jest: {
  fn: (...args: unknown[]) => unknown;
};
