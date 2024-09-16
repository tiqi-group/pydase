import React, { useEffect, useRef, useState } from "react";
import { runMethod } from "../socket";
import { Form, Button, InputGroup, Spinner } from "react-bootstrap";
import { DocStringComponent } from "./DocStringComponent";
import { LevelName } from "./NotificationsComponent";
import useRenderCount from "../hooks/useRenderCount";

export type TaskStatus = "RUNNING" | "NOT_RUNNING";

interface TaskProps {
  fullAccessPath: string;
  docString: string | null;
  status: TaskStatus;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
}

export const TaskComponent = React.memo((props: TaskProps) => {
  const { fullAccessPath, docString, status, addNotification, displayName, id } = props;

  const renderCount = useRenderCount();
  const formRef = useRef(null);
  const [spinning, setSpinning] = useState(false);

  useEffect(() => {
    let message: string;

    if (status === "RUNNING") {
      message = `${fullAccessPath} was started.`;
    } else {
      message = `${fullAccessPath} was stopped.`;
    }

    addNotification(message);
    setSpinning(false);
  }, [status]);

  const execute = async (event: React.FormEvent) => {
    event.preventDefault();

    const method_name = status == "RUNNING" ? "stop" : "start";

    const accessPath = [fullAccessPath, method_name]
      .filter((element) => element)
      .join(".");
    setSpinning(true);
    runMethod(accessPath);
  };

  return (
    <div className="component taskComponent" id={id}>
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
            ) : status === "RUNNING" ? (
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

TaskComponent.displayName = "TaskComponent";
