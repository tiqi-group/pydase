import React, { useEffect, useRef, useState } from "react";
import { runMethod } from "../socket";
import { Form, Button, InputGroup, Spinner } from "react-bootstrap";
import { DocStringComponent } from "./DocStringComponent";
import { LevelName } from "./NotificationsComponent";
import { useRenderCount } from "../hooks/useRenderCount";

interface AsyncMethodProps {
  fullAccessPath: string;
  value: "RUNNING" | null;
  docString: string | null;
  hideOutput?: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
  render: boolean;
}

export const AsyncMethodComponent = React.memo((props: AsyncMethodProps) => {
  const {
    fullAccessPath,
    docString,
    value: runningTask,
    addNotification,
    displayName,
    id,
  } = props;

  // Conditional rendering based on the 'render' prop.
  if (!props.render) {
    return null;
  }

  const renderCount = useRenderCount();
  const formRef = useRef(null);
  const [spinning, setSpinning] = useState(false);
  const name = fullAccessPath.split(".").at(-1)!;
  const parentPath = fullAccessPath.slice(0, -(name.length + 1));

  useEffect(() => {
    let message: string;

    if (runningTask === null) {
      message = `${fullAccessPath} task was stopped.`;
    } else {
      message = `${fullAccessPath} was started.`;
    }
    addNotification(message);
    setSpinning(false);
  }, [props.value]);

  const execute = async (event: React.FormEvent) => {
    event.preventDefault();
    let method_name: string;

    if (runningTask !== undefined && runningTask !== null) {
      method_name = `stop_${name}`;
    } else {
      method_name = `start_${name}`;
    }

    const accessPath = [parentPath, method_name].filter((element) => element).join(".");
    setSpinning(true);
    runMethod(accessPath);
  };

  return (
    <div className="component asyncMethodComponent" id={id}>
      {process.env.NODE_ENV === "development" && <div>Render count: {renderCount}</div>}
      <Form onSubmit={execute} ref={formRef}>
        <InputGroup>
          <InputGroup.Text>
            {displayName}
            <DocStringComponent docString={docString} />
          </InputGroup.Text>
          <Button id={`button-${id}`} type="submit">
            {spinning ? (
              <Spinner size="sm" role="status" aria-hidden="true" />
            ) : runningTask === "RUNNING" ? (
              "Stop "
            ) : (
              "Start "
            )}
          </Button>
        </InputGroup>
      </Form>
    </div>
  );
});

AsyncMethodComponent.displayName = "AsyncMethodComponent";
