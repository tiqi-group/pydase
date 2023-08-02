import React, { useEffect, useRef } from 'react';
import { InputGroup, Form, Row, Col } from 'react-bootstrap';
import { emit_update } from '../socket';
import { DocStringComponent } from './DocStringComponent';

interface EnumComponentProps {
  name: string;
  parent_path: string;
  value: string;
  docString?: string;
  enumDict: Record<string, string>;
}

export const EnumComponent = React.memo((props: EnumComponentProps) => {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });

  const { name, parent_path, value, docString, enumDict } = props;

  const handleValueChange = (newValue: string) => {
    emit_update(name, parent_path, newValue);
  };

  return (
    <div className={'component boolean'} id={parent_path.concat('.' + name)}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}
      <DocStringComponent docString={docString} />
      <Row>
        <Col className="col-5 d-flex align-items-center">
          <InputGroup.Text>{name}</InputGroup.Text>
          <Form.Select
            aria-label="Default select example"
            value={value}
            onChange={(event) => handleValueChange(event.target.value)}>
            {Object.entries(enumDict).map(([key, val]) => (
              <option key={key} value={key}>
                {key} - {val}
              </option>
            ))}
          </Form.Select>
        </Col>
      </Row>
    </div>
  );
});
