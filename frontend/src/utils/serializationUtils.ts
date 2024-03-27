const serializePrimitive = (
  obj: number | boolean | string | null,
  accessPath: string
) => {
  let type: string;

  if (typeof obj === 'number') {
    type = Number.isInteger(obj) ? 'int' : 'float';
    return {
      full_access_path: accessPath,
      doc: null,
      readonly: false,
      type,
      value: obj
    };
  } else if (typeof obj === 'boolean') {
    type = 'bool';
    return {
      full_access_path: accessPath,
      doc: null,
      readonly: false,
      type,
      value: obj
    };
  } else if (typeof obj === 'string') {
    type = 'str';
    return {
      full_access_path: accessPath,
      doc: null,
      readonly: false,
      type,
      value: obj
    };
  } else if (obj === null) {
    type = 'NoneType';
    return {
      full_access_path: accessPath,
      doc: null,
      readonly: false,
      type,
      value: null
    };
  } else {
    throw new Error('Unsupported type for serialization');
  }
};

export const serializeList = (obj: unknown[], accessPath: string = '') => {
  const doc = null;
  const value = obj.map((item, index) => {
    if (
      typeof item === 'number' ||
      typeof item === 'boolean' ||
      typeof item === 'string' ||
      item === null
    ) {
      serializePrimitive(
        item as number | boolean | string | null,
        `${accessPath}[${index}]`
      );
    }
  });

  return {
    full_access_path: accessPath,
    type: 'list',
    value,
    readonly: false,
    doc
  };
};
export const serializeDict = (
  obj: Record<string, unknown>,
  accessPath: string = ''
) => {
  const doc = null;
  const value = Object.entries(obj).reduce((acc, [key, val]) => {
    // Construct the new access path for nested properties
    const newPath = `${accessPath}["${key}"]`;

    // Serialize each value in the dictionary and assign to the accumulator
    if (
      typeof val === 'number' ||
      typeof val === 'boolean' ||
      typeof val === 'string' ||
      val === null
    ) {
      acc[key] = serializePrimitive(val as number | boolean | string | null, newPath);
    }

    return acc;
  }, {});

  return {
    full_access_path: accessPath,
    type: 'dict',
    value,
    readonly: false,
    doc
  };
};
