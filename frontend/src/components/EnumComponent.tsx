import React, { useEffect } from "react";
import { InputGroup, Form, Row, Col } from "react-bootstrap";
import { DocStringComponent } from "./DocStringComponent";
import { LevelName } from "./NotificationsComponent";
import { SerializedObject, SerializedEnum } from "../types/SerializedObject";
import { propsAreEqual } from "../utils/propsAreEqual";
import useRenderCount from "../hooks/useRenderCount";

interface EnumComponentProps extends SerializedEnum {
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
  changeCallback: (value: SerializedObject, callback?: (ack: unknown) => void) => void;
}

export const EnumComponent = React.memo((props: EnumComponentProps) => {
  const {
    addNotification,
    displayName,
    id,
    value,
    full_access_path: fullAccessPath,
    enum: enumDict,
    doc: docString,
    readonly: readOnly,
    changeCallback,
  } = props;

  const renderCount = useRenderCount();

  useEffect(() => {
    addNotification(`${fullAccessPath} changed to ${value}.`);
  }, [value]);

  return (
    <div className={"component enumComponent"} id={id}>
      {process.env.NODE_ENV === "development" && <div>Render count: {renderCount}</div>}
      <Row>
        <Col className="d-flex align-items-center">
          <InputGroup.Text>
            {displayName}
            <DocStringComponent docString={docString} />
          </InputGroup.Text>

          {readOnly ? (
            // Display the Form.Control when readOnly is true
            <Form.Control
              style={
                props.type == "ColouredEnum" ? { backgroundColor: enumDict[value] } : {}
              }
              value={props.type == "ColouredEnum" ? value : enumDict[value]}
              name={fullAccessPath}
              disabled={true}
            />
          ) : (
            // Display the Form.Select when readOnly is false
            <Form.Select
              aria-label="example-select"
              value={value}
              name={fullAccessPath}
              style={
                props.type == "ColouredEnum" ? { backgroundColor: enumDict[value] } : {}
              }
              onChange={(event) =>
                changeCallback({
                  type: props.type,
                  name: props.name,
                  enum: enumDict,
                  value: event.target.value,
                  full_access_path: fullAccessPath,
                  readonly: props.readonly,
                  doc: props.doc,
                })
              }>
              {Object.entries(enumDict).map(([key, val]) => (
                <option key={key} value={key}>
                  {props.type == "ColouredEnum" ? key : val}
                </option>
              ))}
            </Form.Select>
          )}
        </Col>
      </Row>
    </div>
  );
}, propsAreEqual);

EnumComponent.displayName = "EnumComponent";
