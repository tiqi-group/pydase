import React, { useState, useEffect, useRef } from 'react';
import { emit_update } from '../socket';
import { Button, InputGroup, Form, Collapse } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';

interface MethodProps {
  name: string;
  parent_path: string;
  parameters: Record<string, string>;
  docString?: string;
  hideOutput?: boolean;
}

export const MethodComponent = React.memo((props: MethodProps) => {
  const renderCount = useRef(0);
  const [hideOutput, setHideOutput] = useState(false);

  // Add a new state variable to hold the list of function calls
  const [functionCalls, setFunctionCalls] = useState([]);

  const { name, parent_path, docString } = props;

  const execute = async (event: React.FormEvent) => {
    event.preventDefault();

    const args = {};
    Object.keys(props.parameters).forEach(
      (name) => (args[name] = event.target[name].value)
    );
    emit_update(name, parent_path, { args: args }, (ack) => {
      // Update the functionCalls state with the new call if we get an acknowledge msg
      if (ack !== undefined) {
        setFunctionCalls((prevCalls) => [...prevCalls, { name, args, result: ack }]);
      }
    });
  };

  useEffect(() => {
    renderCount.current++;
    if (props.hideOutput !== undefined) {
      setHideOutput(props.hideOutput);
    }
  });

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
    <div
      className="col-5 align-items-center method"
      id={parent_path.concat('.' + name)}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}
      <h5 onClick={() => setHideOutput(!hideOutput)} style={{ cursor: 'pointer' }}>
        Function: {name}
        <DocStringComponent docString={docString} />
      </h5>
      <Form onSubmit={execute}>
        {args}
        <div>
          <Button variant="primary" type="submit">
            Execute
          </Button>
        </div>
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
