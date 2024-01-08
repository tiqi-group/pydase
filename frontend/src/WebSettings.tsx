import { createContext } from 'react';

export const WebSettingsContext = createContext<Record<string, WebSetting>>({});

export type WebSetting = {
  displayName: string;
  index: number;
};
