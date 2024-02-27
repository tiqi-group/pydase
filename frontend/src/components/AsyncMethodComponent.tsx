import React, { useEffect, useRef } from 'react';
import { runMethod } from '../socket';
import { Form, Button, InputGroup } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { LevelName } from './NotificationsComponent';

type AsyncMethodProps = {
  name: string;
  parentPath: string;
  value: 'RUNNING' | null;
  docString?: string;
  hideOutput?: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
  render: boolean;
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

  // Conditional rendering based on the 'render' prop.
  if (!props.render) {
    return null;
  }

  const renderCount = useRef(0);
  const formRef = useRef(null);
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');

  useEffect(() => {
    renderCount.current++;
    let message: string;

    if (runningTask === null) {
      message = `${fullAccessPath} task was stopped.`;
    } else {
      message = `${fullAccessPath} was started.`;
    }
    addNotification(message);
  }, [props.value]);

  const execute = async (event: React.FormEvent) => {
    event.preventDefault();
    let method_name: string;

    if (runningTask !== undefined && runningTask !== null) {
      method_name = `stop_${name}`;
    } else {
      method_name = `start_${name}`;
    }

    runMethod(method_name, parentPath, {});
  };

  return (
    <div className="component asyncMethodComponent" id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <Form onSubmit={execute} ref={formRef}>
        <InputGroup>
          <InputGroup.Text>
            {displayName}
            <DocStringComponent docString={docString} />
          </InputGroup.Text>
          <Button id={`button-${id}`} type="submit">
            {runningTask === 'RUNNING' ? 'Stop ' : 'Start '}
          </Button>
        </InputGroup>
      </Form>
    </div>
  );
});
