import React, { useEffect, useRef } from 'react';
import { emit_update } from '../socket';
import { InputGroup, Form, Button } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';

interface AsyncMethodProps {
  name: string;
  parentPath: string;
  parameters: Record<string, string>;
  value: Record<string, string>;
  docString?: string;
  hideOutput?: boolean;
  addNotification: (message: string) => void;
}

export const AsyncMethodComponent = React.memo((props: AsyncMethodProps) => {
  const { name, parentPath, docString, value: runningTask, addNotification } = props;
  const renderCount = useRef(0);
  const formRef = useRef(null);

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

  useEffect(() => {
    let message: string;

    if (runningTask === null) {
      message = `${parentPath}.${name} task was stopped.`;
    } else {
      const runningTaskEntries = Object.entries(runningTask)
        .map(([key, value]) => `${key}: "${value}"`)
        .join(', ');

      message = `${parentPath}.${name} was started with parameters { ${runningTaskEntries} }.`;
    }
    addNotification(message);
  }, [props.value]);

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

    emit_update(method_name, parentPath, { args: args });
  };

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
      className="align-items-center asyncMethodComponent"
      id={parentPath.concat('.' + name)}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}
      <h5>
        Function: {name}
        <DocStringComponent docString={docString} />
      </h5>
      <Form onSubmit={execute} ref={formRef}>
        {args}
        <Button
          id={`button-${parentPath}.${name}`}
          name={name}
          value={parentPath}
          type="submit">
          {runningTask ? 'Stop' : 'Start'}
        </Button>
      </Form>
    </div>
  );
});
