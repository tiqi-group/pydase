import React, { useEffect, useRef, useState } from 'react';
import { Card, Collapse, Image } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { ChevronDown, ChevronRight } from 'react-bootstrap-icons';
import { getIdFromFullAccessPath } from '../utils/stringUtils';

interface ImageComponentProps {
  name: string;
  parentPath: string;
  value: string;
  readOnly: boolean;
  docString: string;
  format: string;
  addNotification: (message: string) => void;
}

export const ImageComponent = React.memo((props: ImageComponentProps) => {
  const { name, parentPath, value, docString, format, addNotification } = props;

  const renderCount = useRef(0);
  const [open, setOpen] = useState(true);
  const id = getIdFromFullAccessPath(parentPath.concat('.' + name));

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${parentPath}.${name} changed.`);
  }, [props.value]);

  return (
    <div className={'imageComponent'} id={id}>
      <Card>
        <Card.Header
          onClick={() => setOpen(!open)}
          style={{ cursor: 'pointer' }} // Change cursor style on hover
        >
          {name} {open ? <ChevronDown /> : <ChevronRight />}
        </Card.Header>
        <Collapse in={open}>
          <Card.Body>
            {process.env.NODE_ENV === 'development' && (
              <p>Render count: {renderCount.current}</p>
            )}
            <DocStringComponent docString={docString} />
            {/* Your component JSX here */}
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
