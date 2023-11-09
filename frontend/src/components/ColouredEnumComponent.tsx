import React, { useEffect, useRef } from 'react';
import { InputGroup, Form, Row, Col } from 'react-bootstrap';
import { setAttribute } from '../socket';
import { DocStringComponent } from './DocStringComponent';
import { getIdFromFullAccessPath } from '../utils/stringUtils';

interface ColouredEnumComponentProps {
  name: string;
  parentPath: string;
  value: string;
  docString?: string;
  readOnly: boolean;
  enumDict: Record<string, string>;
  addNotification: (message: string) => void;
}

export const ColouredEnumComponent = React.memo((props: ColouredEnumComponentProps) => {
  const {
    name,
    parentPath: parentPath,
    value,
    docString,
    enumDict,
    readOnly,
    addNotification
  } = props;
  const renderCount = useRef(0);
  const id = getIdFromFullAccessPath(parentPath.concat('.' + name));

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
          {readOnly ? (
            // Display the Form.Control when readOnly is true
            <Form.Control
              value={value}
              disabled={true}
              style={{ backgroundColor: enumDict[value] }}
            />
          ) : (
            // Display the Form.Select when readOnly is false
            <Form.Select
              aria-label="coloured-enum-select"
              value={value}
              style={{ backgroundColor: enumDict[value] }}
              onChange={(event) => handleValueChange(event.target.value)}>
              {Object.entries(enumDict).map(([key]) => (
                <option key={key} value={key}>
                  {key}
                </option>
              ))}
            </Form.Select>
          )}
        </Col>
      </Row>
    </div>
  );
});
