import React, { useEffect, useRef } from 'react';
import { runMethod } from '../socket';
import { InputGroup, Form, Button } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { LevelName } from './NotificationsComponent';

type AsyncMethodProps = {
  name: string;
  parentPath: string;
  parameters: Record<string, string>;
  value: Record<string, string>;
  docString?: string;
  hideOutput?: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
};

export const AsyncMethodComponent = React.memo((props: AsyncMethodProps) => {
  const {
    name,
    parentPath,
    docString,
    value: runningTask,
    addNotification,
    displayName,
    id
  } = props;
  const renderCount = useRef(0);
  const formRef = useRef(null);
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');

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
      message = `${fullAccessPath} task was stopped.`;
    } else {
      const runningTaskEntries = Object.entries(runningTask)
        .map(([key, value]) => `${key}: "${value}"`)
        .join(', ');

      message = `${fullAccessPath} was started with parameters { ${runningTaskEntries} }.`;
    }
    addNotification(message);
  }, [props.value]);

  const execute = async (event: React.FormEvent) => {
    event.preventDefault();
    let method_name: string;
    const kwargs: Record<string, unknown> = {};

    if (runningTask !== undefined && runningTask !== null) {
      method_name = `stop_${name}`;
    } else {
      Object.keys(props.parameters).forEach(
        (name) => (kwargs[name] = event.target[name].value)
      );
      method_name = `start_${name}`;
    }

    runMethod(method_name, parentPath, kwargs);
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
    <div className="component asyncMethodComponent" id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <h5>Function: {displayName}</h5>
      <Form onSubmit={execute} ref={formRef}>
        {args}
        <Button id={`button-${id}`} type="submit">
          {runningTask ? 'Stop ' : 'Start '}
          <DocStringComponent docString={docString} />
        </Button>
      </Form>
    </div>
  );
});
