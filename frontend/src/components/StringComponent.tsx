import React, { useEffect, useRef } from 'react';
import { Form, InputGroup } from 'react-bootstrap';
import { socket } from '../socket';
import { DocStringComponent } from './DocStringComponent';

// TODO: add button functionality

interface StringComponentProps {
  name: string;
  parent_path?: string;
  value: string;
  readOnly: boolean;
  docString: string;
}

export const StringComponent = React.memo((props: StringComponentProps) => {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });

  const { name, parent_path, value, readOnly, docString } = props;
  const handleChange = (event) => {
    socket.emit('frontend_update', {
      name: name,
      parent_path: parent_path,
      value: event.target.value
    });
  };

  return (
    <div className={'component boolean'} id={parent_path.concat(name)}>
      <p>Render count: {renderCount.current}</p>
      <DocStringComponent docString={docString} />
      <div className="row">
        <div className="col-5 d-flex">
          <InputGroup>
            <InputGroup.Text>{name}</InputGroup.Text>
            <Form.Control
              type="text"
              value={value}
              disabled={readOnly}
              name={name}
              onChange={handleChange}
            />
          </InputGroup>
        </div>
      </div>
    </div>
  );
});
