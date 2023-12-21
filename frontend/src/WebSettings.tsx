import { createContext } from 'react';

export const WebSettingsContext = createContext({});

export type WebSetting = {
  displayName: string;
  index: number;
}[];
