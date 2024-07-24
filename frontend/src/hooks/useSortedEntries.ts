import { useContext } from "react";
import { WebSettingsContext } from "../WebSettings";
import { SerializedObject } from "../types/SerializedObject";

export default function useSortedEntries(
  props: Record<string, SerializedObject> | SerializedObject[],
) {
  const webSettings = useContext(WebSettingsContext);

  // Get the order for sorting
  const getOrder = (fullAccessPath: string) => {
    return webSettings[fullAccessPath]?.displayOrder ?? Number.MAX_SAFE_INTEGER;
  };

  // Sort entries based on whether props is an array or an object
  let sortedEntries;
  if (Array.isArray(props)) {
    // Need to make copy of array to leave the original array unmodified
    sortedEntries = [...props].sort((objectA, objectB) => {
      return getOrder(objectA.full_access_path) - getOrder(objectB.full_access_path);
    });
  } else {
    sortedEntries = Object.values(props).sort((objectA, objectB) => {
      return getOrder(objectA.full_access_path) - getOrder(objectB.full_access_path);
    });
  }
  return sortedEntries;
}
