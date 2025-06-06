import { useState, useEffect } from "react";
import { authority } from "../socket";

export default function useLocalStorage(key: string, defaultValue: unknown) {
  const [value, setValue] = useState(() => {
    const storedValue = localStorage.getItem(`${authority}:${key}`);
    if (storedValue) {
      return JSON.parse(storedValue);
    }
    return defaultValue;
  });

  useEffect(() => {
    if (value === undefined) return;
    localStorage.setItem(`${authority}:${key}`, JSON.stringify(value));
  }, [value, key]);

  return [value, setValue];
}
