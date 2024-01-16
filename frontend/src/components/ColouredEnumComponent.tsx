import React, { useContext, useEffect, useRef } from 'react';
import { WebSettingsContext } from '../WebSettings';
import { InputGroup, Form, Row, Col } from 'react-bootstrap';
import { setAttribute } from '../socket';
import { DocStringComponent } from './DocStringComponent';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { LevelName } from './NotificationsComponent';

interface ColouredEnumComponentProps {
  name: string;
  parentPath: string;
  value: string;
  docString?: string;
  readOnly: boolean;
  enumDict: Record<string, string>;
  addNotification: (message: string, levelname?: LevelName) => void;
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
