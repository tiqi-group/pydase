import React, { useEffect, useRef } from 'react';
import { InputGroup, Form, Row, Col } from 'react-bootstrap';
import { setAttribute } from '../socket';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { DocStringComponent } from './DocStringComponent';
import { LevelName } from './NotificationsComponent';

interface EnumComponentProps {
  name: string;
  parentPath: string;
  value: string;
  docString?: string;
  enumDict: Record<string, string>;
  addNotification: (message: string, levelname?: LevelName) => void;
}

export const EnumComponent = React.memo((props: EnumComponentProps) => {
  const {
    name,
    parentPath: parentPath,
    value,
    docString,
    enumDict,
    addNotification
  } = props;

  const renderCount = useRef(0);
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');
  const id = getIdFromFullAccessPath(fullAccessPath);

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${parentPath}.${name} changed to ${value}.`);
  }, [props.value]);

  const handleValueChange = (newValue: string) => {
    setAttribute(name, parentPath, newValue);
  };

  return (
    <div className={'enumComponent'} id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <DocStringComponent docString={docString} />
      <Row>
        <Col className="d-flex align-items-center">
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
