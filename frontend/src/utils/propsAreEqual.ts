import deepEqual from "deep-equal";

export const propsAreEqual = <T extends object>(
  prevProps: T,
  nextProps: T,
): boolean => {
  for (const key in nextProps) {
    if (typeof nextProps[key] === "object") {
      if (!deepEqual(prevProps[key], nextProps[key])) {
        return false;
      }
    } else if (!Object.is(prevProps[key], nextProps[key])) {
      return false;
    }
  }
  return true;
};
