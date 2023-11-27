export interface SerializedValue {
  type: string;
  value: Record<string, unknown> | Array<Record<string, unknown>>;
  readonly: boolean;
  doc: string | null;
  async?: boolean;
  parameters?: unknown;
}
export type State = Record<string, SerializedValue> | null;

export function setNestedValueByPath(
  serializationDict: Record<string, SerializedValue>,
  path: string,
  serializedValue: SerializedValue
): Record<string, SerializedValue> {
  const parentPathParts = path.split('.').slice(0, -1);
  const attrName = path.split('.').pop();

  if (!attrName) {
    throw new Error('Invalid path');
  }

  let currentSerializedValue: SerializedValue;
  const newSerializationDict: Record<string, SerializedValue> = JSON.parse(
    JSON.stringify(serializationDict)
  );

  let currentDict = newSerializationDict;

  try {
    for (const pathPart of parentPathParts) {
      currentSerializedValue = getNextLevelDictByKey(currentDict, pathPart, false);
      // @ts-expect-error The value will be of type SerializedValue as we are still
      // looping through the parent parts
      currentDict = currentSerializedValue['value'];
    }

    currentSerializedValue = getNextLevelDictByKey(currentDict, attrName, true);

    Object.assign(currentSerializedValue, serializedValue);
    return newSerializationDict;
  } catch (error) {
    console.error(error);
    return currentDict;
  }
}

function getNextLevelDictByKey(
  serializationDict: Record<string, SerializedValue>,
  attrName: string,
  allowAppend: boolean = false
): SerializedValue {
  const [key, index] = parseListAttrAndIndex(attrName);
  let currentDict: SerializedValue;

  try {
    if (index !== null) {
      if (!serializationDict[key] || !Array.isArray(serializationDict[key]['value'])) {
        throw new Error(`Expected an array at '${key}', but found something else.`);
      }

      if (index < serializationDict[key]['value'].length) {
        currentDict = serializationDict[key]['value'][index];
      } else if (allowAppend && index === serializationDict[key]['value'].length) {
        // Appending to list
        // @ts-expect-error When the index is not null, I expect an array
        serializationDict[key]['value'].push({});
        currentDict = serializationDict[key]['value'][index];
      } else {
        throw new Error(`Index out of range for '${key}[${index}]'.`);
      }
    } else {
      if (!serializationDict[key]) {
        throw new Error(`Key '${key}' not found.`);
      }
      currentDict = serializationDict[key];
    }
  } catch (error) {
    throw new Error(`Error occurred trying to access '${attrName}': ${error}`);
  }

  if (typeof currentDict !== 'object' || currentDict === null) {
    throw new Error(
      `Expected a dictionary at '${attrName}', but found type '${typeof currentDict}' instead.`
    );
  }

  return currentDict;
}

function parseListAttrAndIndex(attrString: string): [string, number | null] {
  let index: number | null = null;
  let attrName = attrString;

  if (attrString.includes('[') && attrString.endsWith(']')) {
    const parts = attrString.split('[');
    attrName = parts[0];
    const indexPart = parts[1].slice(0, -1); // Removes the closing ']'

    if (!isNaN(parseInt(indexPart))) {
      index = parseInt(indexPart);
    } else {
      console.error(`Invalid index format in key: ${attrString}`);
    }
  }

  return [attrName, index];
}
