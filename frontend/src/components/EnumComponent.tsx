import React, { useEffect, useRef } from 'react';
import { InputGroup, Form, Row, Col } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { LevelName } from './NotificationsComponent';

type EnumComponentProps = {
  name: string;
  parentPath: string;
  value: string;
  docString?: string;
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

export const EnumComponent = React.memo((props: EnumComponentProps) => {
  const {
    value,
    docString,
    enumDict,
    addNotification,
    changeCallback = () => {},
    displayName,
    id
  } = props;

  const renderCount = useRef(0);
  const fullAccessPath = [props.parentPath, props.name]
    .filter((element) => element)
    .join('.');

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
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
          <Form.Select
            aria-label="Default select example"
            value={value}
            onChange={(event) => changeCallback(event.target.value)}>
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
