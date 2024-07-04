import { SerializedValue } from '../components/GenericComponent';

export type State = {
  type: string;
  name: string;
  value: Record<string, SerializedValue> | null;
  readonly: boolean;
  doc: string | null;
};

/**
 * Splits a full access path into its atomic parts, separating attribute names, numeric
 * indices (including floating points), and string keys within indices.
 *
 * @param path The full access path string to be split into components.
 * @returns An array of components that make up the path, including attribute names,
 *          numeric indices, and string keys as separate elements.
 */
export function parseFullAccessPath(path: string): string[] {
  // The pattern matches:
  // \w+ - Words
  // \[\d+\.\d+\] - Floating point numbers inside brackets
  // \[\d+\] - Integers inside brackets
  // \["[^"]*"\] - Double-quoted strings inside brackets
  // \['[^']*'\] - Single-quoted strings inside brackets
  const pattern = /\w+|\[\d+\.\d+\]|\[\d+\]|\["[^"]*"\]|\['[^']*'\]/g;
  const matches = path.match(pattern);

  return matches ?? []; // Return an empty array if no matches found
}

/**
 * Parse a serialized key and convert it to an appropriate type (number or string).
 *
 * @param serializedKey The serialized key, which might be enclosed in brackets and quotes.
 * @returns The processed key as a number or an unquoted string.
 *
 * Examples:
 * console.log(parseSerializedKey("attr_name"));  // Outputs: attr_name  (string)
 * console.log(parseSerializedKey("[123]"));      // Outputs: 123  (number)
 * console.log(parseSerializedKey("[12.3]"));     // Outputs: 12.3  (number)
 * console.log(parseSerializedKey("['hello']"));  // Outputs: hello  (string)
 * console.log(parseSerializedKey('["12.34"]'));  // Outputs: "12.34"  (string)
 * console.log(parseSerializedKey('["complex"]'));// Outputs: "complex"  (string)
 */
function parseSerializedKey(serializedKey: string): string | number {
  // Strip outer brackets if present
  if (serializedKey.startsWith('[') && serializedKey.endsWith(']')) {
    serializedKey = serializedKey.slice(1, -1);
  }

  // Strip quotes if the resulting string is quoted
  if (
    (serializedKey.startsWith("'") && serializedKey.endsWith("'")) ||
    (serializedKey.startsWith('"') && serializedKey.endsWith('"'))
  ) {
    return serializedKey.slice(1, -1);
  }

  // Try converting to a number if the string is not quoted
  const parsedNumber = parseFloat(serializedKey);
  if (!isNaN(parsedNumber)) {
    return parsedNumber;
  }

  // Return the original string if it's not a valid number
  return serializedKey;
}

function getOrCreateItemInContainer(
  container: Record<string | number, SerializedValue> | SerializedValue[],
  key: string | number,
  allowAddKey: boolean
): SerializedValue {
  // Check if the key exists and return the item if it does
  if (key in container) {
    return container[key];
  }

  // Handling the case where the key does not exist
  if (Array.isArray(container)) {
    // Handling arrays
    if (allowAddKey && key === container.length) {
      container.push(createEmptySerializedObject());
      return container[key];
    }
    throw new Error(`Index out of bounds: ${key}`);
  } else {
    // Handling objects
    if (allowAddKey) {
      container[key] = createEmptySerializedObject();
      return container[key];
    }
    throw new Error(`Key not found: ${key}`);
  }
}

/**
 * Retrieve an item from a container specified by the passed key. Add an item to the
 * container if allowAppend is set to True.
 *
 * @param container Either a dictionary or list of serialized objects.
 * @param key The key name or index (as a string) representing the attribute in the container.
 * @param allowAppend Whether to allow appending a new entry if the specified index is out of range by exactly one position.
 * @returns The serialized object corresponding to the specified key.
 * @throws SerializationPathError If the key is invalid or leads to an access error without append permissions.
 * @throws SerializationValueError If the expected structure is incorrect.
 */
function getContainerItemByKey(
  container: Record<string, SerializedValue> | SerializedValue[],
  key: string,
  allowAppend: boolean = false
): SerializedValue {
  const processedKey = parseSerializedKey(key);

  try {
    return getOrCreateItemInContainer(container, processedKey, allowAppend);
  } catch (error) {
    if (error instanceof RangeError) {
      throw new Error(`Index '${processedKey}': ${error.message}`);
    } else if (error instanceof Error) {
      throw new Error(`Key '${processedKey}': ${error.message}`);
    }
    throw error; // Re-throw if it's not a known error type
  }
}

export function setNestedValueByPath(
  serializationDict: Record<string, SerializedValue>,
  path: string,
  serializedValue: SerializedValue
): Record<string, SerializedValue> {
  const pathParts = parseFullAccessPath(path);
  const newSerializationDict: Record<string, SerializedValue> = JSON.parse(
    JSON.stringify(serializationDict)
  );

  let currentDict = newSerializationDict;

  try {
    for (let i = 0; i < pathParts.length - 1; i++) {
      const pathPart = pathParts[i];
      const nextLevelSerializedObject = getContainerItemByKey(
        currentDict,
        pathPart,
        false
      );
      currentDict = nextLevelSerializedObject['value'] as Record<
        string,
        SerializedValue
      >;
    }

    const finalPart = pathParts[pathParts.length - 1];
    const finalObject = getContainerItemByKey(currentDict, finalPart, true);

    Object.assign(finalObject, serializedValue);

    return newSerializationDict;
  } catch (error) {
    console.error(`Error occurred trying to change ${path}: ${error}`);
  }
}

function createEmptySerializedObject(): SerializedValue {
  return {
    full_access_path: '',
    value: undefined,
    type: 'None',
    doc: null,
    readonly: false
  };
}
