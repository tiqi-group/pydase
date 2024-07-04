import React, { useEffect, useRef, useState } from "react";
import { Card, Collapse, Image } from "react-bootstrap";
import { DocStringComponent } from "./DocStringComponent";
import { ChevronDown, ChevronRight } from "react-bootstrap-icons";
import { LevelName } from "./NotificationsComponent";

type ImageComponentProps = {
  fullAccessPath: string;
  value: string;
  docString: string | null;
  format: string;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
};

export const ImageComponent = React.memo((props: ImageComponentProps) => {
  const { fullAccessPath, value, docString, format, addNotification, displayName, id } =
    props;

  const renderCount = useRef(0);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${fullAccessPath} changed.`);
  }, [props.value]);

  return (
    <div className="component imageComponent" id={id}>
      <Card>
        <Card.Header
          onClick={() => setOpen(!open)}
          style={{ cursor: "pointer" }} // Change cursor style on hover
        >
          {displayName}
          <DocStringComponent docString={docString} />
          {open ? <ChevronDown /> : <ChevronRight />}
        </Card.Header>
        <Collapse in={open}>
          <Card.Body>
            {process.env.NODE_ENV === "development" && (
              <p>Render count: {renderCount.current}</p>
            )}
            {format === "" && value === "" ? (
              <p>No image set in the backend.</p>
            ) : (
              <Image src={`data:image/${format.toLowerCase()};base64,${value}`}></Image>
            )}
          </Card.Body>
        </Collapse>
      </Card>
    </div>
  );
});

ImageComponent.displayName = "ImageComponent";
