import { useEffect, useReducer } from 'react';
import { ButtonComponent } from './components/ButtonComponent';
import { NumberComponent } from './components/NumberComponent';
import { SliderComponent } from './components/SliderComponent';
import { EnumComponent } from './components/EnumComponent';
import { socket } from './socket';
import { MethodComponent } from './components/MethodComponent';
import { AsyncMethodComponent } from './components/AsyncMethodComponent';

type AttributeType =
  | 'str'
  | 'bool'
  | 'float'
  | 'int'
  | 'method'
  | 'DataService'
  | 'Enum'
  | 'NumberSlider';

type ValueType = boolean | string | number | object;
interface Attribute {
  type: AttributeType;
  value?: ValueType;
  readonly: boolean;
  doc?: string | null;
  parameters?: Record<string, string>;
  async?: boolean;
  enum?: Record<string, string>;
}

type MyData = Record<string, Attribute>;
type State = MyData | null;
type Action =
  | { type: 'SET_DATA'; data: MyData }
  | { type: 'UPDATE_ATTRIBUTE'; parent_path: string; name: string; value: ValueType };
type NotificationElement = {
  data: { parent_path: string; name: string; value: object };
};

/**
 * A function to update a specific property in a deeply nested object.
 * The property to be updated is specified by a path array.
 *
 * @param {Array<string>} path - An array where each element is a key in the object,
 * forming a path to the property to be updated.
 * @param {object} obj - The object to be updated.
 * @param {object} value - The new value for the property specified by the path.
 * @return {object} - A new object with the specified property updated.
 */
function updateNestedObject(path: Array<string>, obj: object, value: ValueType) {
  // Base case: If the path is empty, return the new value.
  // This means we've reached the nested property to be updated.
  if (path.length === 0) {
    return value;
  }

  // Recursive case: If the path is not empty, split it into the first key and the rest
  // of the path.
  const [first, ...rest] = path;

  // Return a new object that copies all properties of the original object, but updates
  // the property specified by 'first'.
  // The updated property is an object that copies all properties of the original nested
  // object, but updates the 'value' property.
  // The new 'value' property is the result of a recursive call to updateNestedObject,
  // with the rest of the path, the value of the nested object as the object to be
  // updated, and the new value.
  return {
    ...obj,
    [first]: {
      ...obj[first],
      value: updateNestedObject(rest, obj[first]?.value || {}, value)
    }
  };
}

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'SET_DATA':
      return action.data;
    case 'UPDATE_ATTRIBUTE': {
      const path = action.parent_path.split('.').slice(1).concat(action.name);

      return updateNestedObject(path, state, action.value);
    }
    default:
      throw new Error();
  }
};

const App = () => {
  const [state, dispatch] = useReducer(reducer, null);
  // const [isConnected, setIsConnected] = useState(socket.connected);

  useEffect(() => {
    // Fetch data from the API when the component mounts
    fetch('http://localhost:8001/service-properties')
      .then((response) => response.json())
      .then((data: MyData) => dispatch({ type: 'SET_DATA', data }));

    function onNotify(value: NotificationElement) {
      dispatch({
        type: 'UPDATE_ATTRIBUTE',
        parent_path: value.data.parent_path,
        name: value.data.name,
        value: value.data.value
      });
    }

    socket.on('notify', onNotify);

    return () => {
      socket.off('notify', onNotify);
    };
  }, []);

  // While the data is loading
  if (!state) {
    return <p>Loading...</p>;
  }
  return (
    <div className="App">
      {Object.entries(state).map(([key, value]) => {
        if (value.type === 'bool') {
          return (
            <div key={key}>
              <ButtonComponent
                name={key}
                parent_path="DataService"
                docString={value.doc}
                readOnly={value.readonly}
                value={Boolean(value.value)}
              />
            </div>
          );
        } else if (value.type === 'float' || value.type === 'int') {
          return (
            <div key={key}>
              <NumberComponent
                name={key}
                type={value.type}
                parent_path="DataService"
                docString={value.doc}
                readOnly={value.readonly}
                value={Number(value.value)}
              />
            </div>
          );
        } else if (value.type === 'NumberSlider') {
          return (
            <div key={key}>
              <SliderComponent
                name={key}
                parent_path="DataService"
                docString={value.doc}
                readOnly={value.readonly}
                value={value.value['value']['value']}
                min={value.value['min']['value']}
                max={value.value['max']['value']}
                stepSize={value.value['step_size']['value']}
              />
            </div>
          );
        } else if (value.type === 'Enum') {
          return (
            <div key={key}>
              <EnumComponent
                name={key}
                parent_path="DataService"
                docString={value.doc}
                value={String(value.value)}
                enumDict={value.enum}
              />
            </div>
          );
        } else if (value.type === 'method') {
          if (!value.async) {
            return (
              <div key={key}>
                <MethodComponent
                  name={key}
                  parent_path="DataService"
                  docString={value.doc}
                  parameters={value.parameters}
                />
              </div>
            );
          } else {
            return (
              <div key={key}>
                <AsyncMethodComponent
                  name={key}
                  parent_path="DataService"
                  docString={value.doc}
                  parameters={value.parameters}
                  value={value.value as Record<string, string>}
                />
              </div>
            );
          }
        } else {
          return <div key={key}></div>;
        }
      })}
    </div>
  );
};

export default App;
