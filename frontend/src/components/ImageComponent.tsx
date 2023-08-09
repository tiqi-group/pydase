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
  // Define your component specific props here
}

export const ImageComponent = React.memo((props: ImageComponentProps) => {
  const renderCount = useRef(0);
  const { name, parentPath, value, docString } = props;
  // Your component logic here

  useEffect(() => {
    renderCount.current++;
    console.log(value);
  });

  return (
    <div className={'imageComponent'} id={parentPath.concat('.' + name)}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}
      <DocStringComponent docString={docString} />
      {/* Your component JSX here */}
      <Card>
        <Card.Header
          style={{ cursor: 'pointer' }} // Change cursor style on hover
        >
          {name}
        </Card.Header>
        <Image src={`data:image/jpeg;base64,${value}`}></Image>
      </Card>
    </div>
  );
});
