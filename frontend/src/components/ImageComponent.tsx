import React, { useEffect, useRef, useState } from 'react';
import { Card, Collapse, Image } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { ChevronDown, ChevronRight } from 'react-bootstrap-icons';
import { LevelName } from './NotificationsComponent';

type ImageComponentProps = {
  name: string;
  parentPath: string;
  value: string;
  docString: string;
  format: string;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
};

export const ImageComponent = React.memo((props: ImageComponentProps) => {
  const { value, docString, format, addNotification, displayName, id } = props;

  const renderCount = useRef(0);
  const [open, setOpen] = useState(true);
  const fullAccessPath = [props.parentPath, props.name]
    .filter((element) => element)
    .join('.');

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
          style={{ cursor: 'pointer' }} // Change cursor style on hover
        >
          {displayName}
          <DocStringComponent docString={docString} />
          {open ? <ChevronDown /> : <ChevronRight />}
        </Card.Header>
        <Collapse in={open}>
          <Card.Body>
            {process.env.NODE_ENV === 'development' && (
              <p>Render count: {renderCount.current}</p>
            )}
            {format === '' && value === '' ? (
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
