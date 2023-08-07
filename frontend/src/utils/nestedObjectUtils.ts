type Data = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
};

const STANDARD_TYPES = [
  'int',
  'float',
  'bool',
  'str',
  'Enum',
  'method',
  'NoneType',
  'Quantity'
];

export function getDataServiceJSONValueByPathAndKey(
  data: Data,
  path: string,
  key = 'value'
): string {
  // Split the path into parts
  const parts = path.split(/\.|(?=\[\d+\])/);
  parts.shift(); // Remove the first element

  // Traverse the dictionary according to the path parts
  for (const part of parts) {
    if (part.startsWith('[')) {
      // List index
      const idx = parseInt(part.substring(1, part.length - 1)); // Strip the brackets and convert to integer
      data = data[idx];
    } else {
      // Dictionary key
      data = data[part];
    }

    // When the attribute is a class instance, the attributes are nested in the
    // "value" key
    if (!STANDARD_TYPES.includes(data['type'])) {
      data = data['value'];
    }
  }

  // Return the value at the terminal point of the path
  return data[key];
}
