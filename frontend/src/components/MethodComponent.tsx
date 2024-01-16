import React, { useContext, useEffect, useRef, useState } from 'react';
import { WebSettingsContext } from '../WebSettings';
import { runMethod } from '../socket';
import { Button, InputGroup, Form, Collapse } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { LevelName } from './NotificationsComponent';

interface MethodProps {
  name: string;
  parentPath: string;
  parameters: Record<string, string>;
  docString?: string;
  hideOutput?: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
}

export const MethodComponent = React.memo((props: MethodProps) => {
  const { name, parentPath, docString, addNotification } = props;

  const renderCount = useRef(0);
  const [hideOutput, setHideOutput] = useState(false);
  // Add a new state variable to hold the list of function calls
  const [functionCalls, setFunctionCalls] = useState([]);
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');
  const id = getIdFromFullAccessPath(fullAccessPath);
  const webSettings = useContext(WebSettingsContext);
  let displayName = name;

  if (webSettings[fullAccessPath] && webSettings[fullAccessPath].displayName) {
    displayName = webSettings[fullAccessPath].displayName;
  }

  useEffect(() => {
    renderCount.current++;
    if (props.hideOutput !== undefined) {
      setHideOutput(props.hideOutput);
    }
  });

  const triggerNotification = (args: Record<string, string>) => {
    const argsString = Object.entries(args)
      .map(([key, value]) => `${key}: "${value}"`)
      .join(', ');
    let message = `Method ${parentPath}.${name} was triggered`;

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
    Object.keys(props.parameters).forEach(
      (name) => (kwargs[name] = event.target[name].value)
    );
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

  const args = Object.entries(props.parameters).map(([name, type], index) => {
    const form_name = `${name} (${type})`;
    return (
      <InputGroup key={index}>
        <InputGroup.Text className="component-label">{form_name}</InputGroup.Text>
        <Form.Control type="text" name={name} />
      </InputGroup>
    );
  });

  return (
    <div className="align-items-center methodComponent" id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <h5 onClick={() => setHideOutput(!hideOutput)} style={{ cursor: 'pointer' }}>
        Function: {displayName}
      </h5>
      <Form onSubmit={execute}>
        {args}
        <Button variant="primary" type="submit">
          Execute
          <DocStringComponent docString={docString} />
        </Button>
      </Form>

      <Collapse in={!hideOutput}>
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
      </Collapse>
    </div>
  );
});
