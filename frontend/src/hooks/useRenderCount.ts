import { useRef, useEffect } from "react";

export default function useRenderCount() {
  const count = useRef(0);

  useEffect(() => {
    count.current += 1;
  });

  return count.current;
}
