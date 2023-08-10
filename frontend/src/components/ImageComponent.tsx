import React, { useEffect, useRef } from 'react';
import { emit_update } from '../socket';
import { Card, Image } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';

interface ImageComponentProps {
  name: string;
  parentPath: string;
  value: string;
  readOnly: boolean;
  docString: string;
  format: string;
}

export const ImageComponent = React.memo((props: ImageComponentProps) => {
  const renderCount = useRef(0);
  const { name, parentPath, value, docString, format } = props;

  useEffect(() => {
    renderCount.current++;
  });

  return (
    <div className={'imageComponent'} id={parentPath.concat('.' + name)}>
      <Card>
        <Card.Header
          style={{ cursor: 'pointer' }} // Change cursor style on hover
        >
          {name}
        </Card.Header>

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
      </Card>
    </div>
  );
});
