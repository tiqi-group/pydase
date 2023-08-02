import React, { useEffect, useRef } from 'react';
import { socket } from '../socket';
import { InputGroup, Form, Button } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';

interface AsyncMethodProps {
  name: string;
  parent_path: string;
  parameters: Record<string, string>;
  value: Record<string, string>;
  docString?: string;
  hideOutput?: boolean;
}

export const AsyncMethodComponent = React.memo((props: AsyncMethodProps) => {
  const renderCount = useRef(0);
  const formRef = useRef(null);
  const { name, parent_path, docString, value: runningTask } = props;

  const execute = async (event: React.FormEvent) => {
    event.preventDefault();
    let method_name: string;
    const args = {};

    if (runningTask !== undefined && runningTask !== null) {
      method_name = `stop_${name}`;
    } else {
      Object.keys(props.parameters).forEach(
        (name) => (args[name] = event.target[name].value)
      );
      method_name = `start_${name}`;
    }

    socket.emit('frontend_update', {
      name: method_name,
      value: { args: args }
    });
  };

  useEffect(() => {
    renderCount.current++;

    // updates the value of each form control that has a matching name in the
    // runningTask object
    if (runningTask) {
      const formElement = formRef.current;
      if (formElement) {
        Object.entries(runningTask).forEach(([name, value]) => {
          const inputElement = formElement.elements.namedItem(name);
          if (inputElement) {
            inputElement.value = value;
          }
        });
      }
    }
  }, [runningTask]);

  const args = Object.entries(props.parameters).map(([name, type], index) => {
    const form_name = `${name} (${type})`;
    const value = runningTask && runningTask[name];
    const isRunning = value !== undefined && value !== null;

    return (
      <InputGroup key={index}>
        <InputGroup.Text className="component-label">{form_name}</InputGroup.Text>
        <Form.Control
          type="text"
          name={name}
          defaultValue={isRunning ? value : ''}
          disabled={isRunning}
        />
      </InputGroup>
    );
  });

  return (
    <div
      className="col-5 align-items-center method"
      id={parent_path.concat('.' + name)}>
      <p>Render count: {renderCount.current}</p>
      <h5>
        Function: {name}
        <DocStringComponent docString={docString} />
      </h5>
      <Form onSubmit={execute} ref={formRef}>
        {args}
        <Button
          id={`button-${parent_path}.${name}`}
          name={name}
          value={parent_path}
          type="submit">
          {runningTask ? 'Stop' : 'Start'}
        </Button>
      </Form>
    </div>
  );
});
