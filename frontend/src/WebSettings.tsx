import { createContext } from "react";

export const WebSettingsContext = createContext<Record<string, WebSetting>>({});

export interface WebSetting {
  displayName: string;
  display: boolean;
  index: number;
}
