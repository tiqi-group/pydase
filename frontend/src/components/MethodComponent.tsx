import React, { useRef } from "react";
import { runMethod } from "../socket";
import { Button, Form } from "react-bootstrap";
import { DocStringComponent } from "./DocStringComponent";
import { LevelName } from "./NotificationsComponent";
import useRenderCount from "../hooks/useRenderCount";
import { propsAreEqual } from "../utils/propsAreEqual";

interface MethodProps {
  fullAccessPath: string;
  docString: string | null;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
  render: boolean;
}

export const MethodComponent = React.memo((props: MethodProps) => {
  const { fullAccessPath, docString, addNotification, displayName, id } = props;

  // Conditional rendering based on the 'render' prop.
  if (!props.render) {
    return null;
  }

  const renderCount = useRenderCount();
  const formRef = useRef(null);

  const triggerNotification = () => {
    const message = `Method ${fullAccessPath} was triggered.`;

    addNotification(message);
  };

  const execute = async (event: React.FormEvent) => {
    event.preventDefault();
    runMethod(fullAccessPath);

    triggerNotification();
  };

  return (
    <div className="component methodComponent" id={id}>
      {process.env.NODE_ENV === "development" && <div>Render count: {renderCount}</div>}
      <Form onSubmit={execute} ref={formRef}>
        <Button className="component" variant="primary" type="submit">
          {`${displayName} `}
          <DocStringComponent docString={docString} />
        </Button>
      </Form>
    </div>
  );
}, propsAreEqual);

MethodComponent.displayName = "MethodComponent";
