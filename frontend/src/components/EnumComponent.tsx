import React, { useEffect, useRef, useState } from 'react';
import { InputGroup, Form, Row, Col } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { SerializedValue } from './GenericComponent';
import { LevelName } from './NotificationsComponent';

export type EnumSerialization = {
  type: 'Enum' | 'ColouredEnum';
  full_access_path: string;
  name: string;
  value: string;
  readonly: boolean;
  doc?: string | null;
  enum: Record<string, string>;
};

type EnumComponentProps = {
  attribute: EnumSerialization;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
  changeCallback?: (value: SerializedValue, callback?: (ack: unknown) => void) => void;
};

export const EnumComponent = React.memo((props: EnumComponentProps) => {
  const { attribute, addNotification, displayName, id } = props;
  const {
    full_access_path: fullAccessPath,
    value,
    doc: docString,
    enum: enumDict,
    readonly: readOnly
  } = attribute;

  let { changeCallback } = props;
  if (changeCallback === undefined) {
    changeCallback = (value: SerializedValue) => {
      setEnumValue(() => {
        return String(value.value);
      });
    };
  }
  const renderCount = useRef(0);
  const [enumValue, setEnumValue] = useState(value);

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    setEnumValue(() => {
      return value;
    });
    addNotification(`${fullAccessPath} changed to ${value}.`);
  }, [value]);

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
              value={enumDict[enumValue]}
              name={fullAccessPath}
              disabled={true}
            />
          ) : (
            // Display the Form.Select when readOnly is false
            <Form.Select
              aria-label="example-select"
              value={enumValue}
              name={fullAccessPath}
              style={
                attribute.type == 'ColouredEnum'
                  ? { backgroundColor: enumDict[enumValue] }
                  : {}
              }
              onChange={(event) =>
                changeCallback({
                  type: attribute.type,
                  name: attribute.name,
                  enum: enumDict,
                  value: event.target.value,
                  full_access_path: fullAccessPath,
                  readonly: attribute.readonly,
                  doc: attribute.doc
                })
              }>
              {Object.entries(enumDict).map(([key, val]) => (
                <option key={key} value={key}>
                  {attribute.type == 'ColouredEnum' ? key : val}
                </option>
              ))}
            </Form.Select>
          )}
        </Col>
      </Row>
    </div>
  );
});
