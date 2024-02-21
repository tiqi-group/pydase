import React, { useEffect, useRef, useState } from 'react';
import { runMethod } from '../socket';
import { Button, Form, Card } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { LevelName } from './NotificationsComponent';
import { SerializedValue } from './GenericComponent';
import { FloatObject, NumberComponent, QuantityObject } from './NumberComponent';
import { StringComponent } from './StringComponent';
import { ColouredEnumComponent } from './ColouredEnumComponent';
import { EnumComponent } from './EnumComponent';

type MethodProps = {
  name: string;
  parentPath: string;
  parameters: Record<string, SerializedValue>;
  docString?: string;
  hideOutput?: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
};

export const MethodComponent = React.memo((props: MethodProps) => {
  const { name, parentPath, docString, addNotification, displayName, id } = props;

  const renderCount = useRef(0);
  // Add a new state variable to hold the list of function calls
  const [functionCalls, setFunctionCalls] = useState([]);
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');

  const triggerNotification = (args: Record<string, string>) => {
    const argsString = Object.entries(args)
      .map(([key, value]) => `${key}: "${value}"`)
      .join(', ');
    let message = `Method ${fullAccessPath} was triggered`;

    if (argsString === '') {
      message += '.';
    } else {
      message += ` with arguments {${argsString}}.`;
    }
    addNotification(message);
  };

  const execute = async (event: React.FormEvent) => {
    event.preventDefault();
    const kwargs = {};
    Object.keys(props.parameters).forEach((name) => {
      kwargs[name] = event.target[name].value;
    });
    runMethod(name, parentPath, kwargs, (ack) => {
      // Update the functionCalls state with the new call if we get an acknowledge msg
      if (ack !== undefined) {
        setFunctionCalls((prevCalls) => [
          ...prevCalls,
          { name, args: kwargs, result: ack }
        ]);
      }
    });

    triggerNotification(kwargs);
  };

  const args = Object.entries(props.parameters).map(([name, serializedValue]) => {
    if (serializedValue.type == 'float' || serializedValue.type == 'int') {
      return (
        <NumberComponent
          name={name}
          value={(serializedValue as FloatObject).value}
          displayName={name}
          type={serializedValue.type}
          readOnly={false}
          docString={undefined}
          isInstantUpdate={false}
          addNotification={() => {}}
          id={id + '.' + name}
        />
      );
    } else if (serializedValue.type == 'Quantity') {
      return (
        <NumberComponent
          name={name}
          value={(serializedValue as QuantityObject).value.magnitude}
          displayName={name}
          unit={(serializedValue as QuantityObject).value.unit}
          type="float"
          readOnly={false}
          docString={undefined}
          isInstantUpdate={false}
          addNotification={() => {}}
          id={id + '.' + name}
        />
      );
    } else if (serializedValue.type == 'str') {
      return (
        <StringComponent
          name={name}
          value={serializedValue.value as string}
          displayName={name}
          readOnly={false}
          docString={undefined}
          isInstantUpdate={false}
          addNotification={() => {}}
          id={id + '.' + name}
        />
      );
    } else if (serializedValue.type == 'Enum') {
      return (
        <EnumComponent
          name={name}
          parentPath={parentPath}
          value={serializedValue.value as string}
          readOnly={false}
          docString={undefined}
          addNotification={() => {}}
          enumDict={serializedValue.enum}
          displayName={name}
          id={id + '.' + name}
        />
      );
    } else if (serializedValue.type == 'ColouredEnum') {
      return (
        <ColouredEnumComponent
          name={name}
          parentPath={parentPath}
          value={serializedValue.value as string}
          readOnly={false}
          docString={undefined}
          addNotification={() => {}}
          enumDict={serializedValue.enum}
          displayName={name}
          id={id + '.' + name}
        />
      );
    }
  });

  // Content conditionally rendered based on args
  const formContent = (
    <Form onSubmit={execute}>
      {args}
      <Button className="component" variant="primary" type="submit">
        {`${displayName} `}
        <DocStringComponent docString={docString} />
      </Button>
    </Form>
  );

  const outputContent = (
    <div id="function-output">
      {functionCalls.map((call, index) => (
        <div key={index}>
          <div style={{ color: 'grey', fontSize: 'small' }}>
            {Object.entries(call.args)
              .map(([key, val]) => `${key}=${JSON.stringify(val)}`)
              .join(', ') +
              ' => ' +
              JSON.stringify(call.result)}
          </div>
        </div>
      ))}
    </div>
  );

  useEffect(() => {
    renderCount.current++;
  });

  return (
    <div className="component methodComponent" id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      {args.length > 0 ? (
        <Card>
          <Card.Body>
            {formContent}
            {outputContent}
          </Card.Body>
        </Card>
      ) : (
        <div>{formContent}</div>
      )}
    </div>
  );
});
