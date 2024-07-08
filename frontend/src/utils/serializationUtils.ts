import { SerializedObject } from "../types/SerializedObject";

const serializePrimitive = (
  obj: number | boolean | string | null,
  accessPath: string,
): SerializedObject => {
  if (typeof obj === "number") {
    return {
      full_access_path: accessPath,
      doc: null,
      readonly: false,
      type: Number.isInteger(obj) ? "int" : "float",
      value: obj,
    };
  } else if (typeof obj === "boolean") {
    return {
      full_access_path: accessPath,
      doc: null,
      readonly: false,
      type: "bool",
      value: obj,
    };
  } else if (typeof obj === "string") {
    return {
      full_access_path: accessPath,
      doc: null,
      readonly: false,
      type: "str",
      value: obj,
    };
  } else if (obj === null) {
    return {
      full_access_path: accessPath,
      doc: null,
      readonly: false,
      type: "None",
      value: null,
    };
  } else {
    throw new Error("Unsupported type for serialization");
  }
};

export const serializeList = (obj: unknown[], accessPath = "") => {
  const doc = null;
  const value = obj.map((item, index) => {
    if (
      typeof item === "number" ||
      typeof item === "boolean" ||
      typeof item === "string" ||
      item === null
    ) {
      serializePrimitive(
        item as number | boolean | string | null,
        `${accessPath}[${index}]`,
      );
    }
  });

  return {
    full_access_path: accessPath,
    type: "list",
    value,
    readonly: false,
    doc,
  };
};
export const serializeDict = (obj: Record<string, unknown>, accessPath = "") => {
  const doc = null;
  const value = Object.entries(obj).reduce(
    (acc, [key, val]) => {
      // Construct the new access path for nested properties
      const newPath = `${accessPath}["${key}"]`;

      // Serialize each value in the dictionary and assign to the accumulator
      if (
        typeof val === "number" ||
        typeof val === "boolean" ||
        typeof val === "string" ||
        val === null
      ) {
        acc[key] = serializePrimitive(val as number | boolean | string | null, newPath);
      }

      return acc;
    },
    {} as Record<string, SerializedObject>,
  );

  return {
    full_access_path: accessPath,
    type: "dict",
    value,
    readonly: false,
    doc,
  };
};
