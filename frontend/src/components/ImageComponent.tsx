import React, { useContext, useEffect, useRef, useState } from 'react';
import { WebSettingsContext } from '../WebSettings';
import { Card, Collapse, Image } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { ChevronDown, ChevronRight } from 'react-bootstrap-icons';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { LevelName } from './NotificationsComponent';

type ImageComponentProps = {
  name: string;
  parentPath: string;
  value: string;
  readOnly: boolean;
  docString: string;
  format: string;
  addNotification: (message: string, levelname?: LevelName) => void;
};

export const ImageComponent = React.memo((props: ImageComponentProps) => {
  const { name, parentPath, value, docString, format, addNotification } = props;

  const renderCount = useRef(0);
  const [open, setOpen] = useState(true);
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');
  const id = getIdFromFullAccessPath(fullAccessPath);
  const webSettings = useContext(WebSettingsContext);
  let displayName = name;

  if (webSettings[fullAccessPath] && webSettings[fullAccessPath].displayName) {
    displayName = webSettings[fullAccessPath].displayName;
  }

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${parentPath}.${name} changed.`);
  }, [props.value]);

  return (
    <div className={'imageComponent'} id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
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
