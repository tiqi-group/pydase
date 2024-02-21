import React, { useEffect, useRef, useState } from 'react';
import { InputGroup, Form, Row, Col } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { LevelName } from './NotificationsComponent';

type ColouredEnumComponentProps = {
  name: string;
  parentPath: string;
  value: string;
  docString?: string;
  readOnly: boolean;
  enumDict: Record<string, string>;
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (
    value: unknown,
    attributeName?: string,
    prefix?: string,
    callback?: (ack: unknown) => void
  ) => void;
  displayName: string;
  id: string;
};

export const ColouredEnumComponent = React.memo((props: ColouredEnumComponentProps) => {
  const {
    name,
    value,
    docString,
    enumDict,
    readOnly,
    addNotification,
    displayName,
    id
  } = props;
  let { changeCallback } = props;
  if (changeCallback === undefined) {
    changeCallback = (value: string) => {
      setEnumValue(() => {
        return value;
      });
    };
  }

  const renderCount = useRef(0);
  const [enumValue, setEnumValue] = useState(value);

  const fullAccessPath = [props.parentPath, props.name]
    .filter((element) => element)
    .join('.');

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    setEnumValue(() => {
      return props.value;
    });
    addNotification(`${fullAccessPath} changed to ${value}.`);
  }, [props.value]);

  return (
    <div className={'component enumComponent'} id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <Row>
        <Col className="d-flex align-items-center">
          <InputGroup.Text>
            {displayName}
            <DocStringComponent docString={docString} />
          </InputGroup.Text>
          {readOnly ? (
            // Display the Form.Control when readOnly is true
            <Form.Control
              value={enumValue}
              name={name}
              disabled={true}
              style={{ backgroundColor: enumDict[enumValue] }}
            />
          ) : (
            // Display the Form.Select when readOnly is false
            <Form.Select
              aria-label="coloured-enum-select"
              value={enumValue}
              name={name}
              style={{ backgroundColor: enumDict[enumValue] }}
              onChange={(event) => changeCallback(event.target.value)}>
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
