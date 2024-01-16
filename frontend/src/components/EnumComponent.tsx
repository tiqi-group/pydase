import React, { useContext, useEffect, useRef } from 'react';
import { WebSettingsContext } from '../WebSettings';
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
  const webSettings = useContext(WebSettingsContext);
  let displayName = name;

  if (webSettings[fullAccessPath] && webSettings[fullAccessPath].displayName) {
    displayName = webSettings[fullAccessPath].displayName;
  }

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
      <Row>
        <Col className="d-flex align-items-center">
          <InputGroup.Text>
            {displayName}
            <DocStringComponent docString={docString} />
          </InputGroup.Text>
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
