import React, { useEffect, useRef, useState } from "react";
import { InputGroup, Form, Row, Col, Collapse, ToggleButton } from "react-bootstrap";
import { DocStringComponent } from "./DocStringComponent";
import { Slider } from "@mui/material";
import { NumberComponent, NumberObject } from "./NumberComponent";
import { LevelName } from "./NotificationsComponent";
import { SerializedObject } from "../types/SerializedObject";
import { QuantityMap } from "../types/QuantityMap";

interface SliderComponentProps {
  fullAccessPath: string;
  min: NumberObject;
  max: NumberObject;
  value: NumberObject;
  readOnly: boolean;
  docString: string | null;
  stepSize: NumberObject;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (value: SerializedObject, callback?: (ack: unknown) => void) => void;
  displayName: string;
  id: string;
}

export const SliderComponent = React.memo((props: SliderComponentProps) => {
  const renderCount = useRef(0);
  const [open, setOpen] = useState(false);
  const {
    fullAccessPath,
    value,
    min,
    max,
    stepSize,
    docString,
    isInstantUpdate,
    addNotification,
    changeCallback = () => {},
    displayName,
    id,
  } = props;

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${fullAccessPath} changed to ${value.value}.`);
  }, [props.value]);

  useEffect(() => {
    addNotification(`${fullAccessPath}.min changed to ${min.value}.`);
  }, [props.min]);

  useEffect(() => {
    addNotification(`${fullAccessPath}.max changed to ${max.value}.`);
  }, [props.max]);

  useEffect(() => {
    addNotification(`${fullAccessPath}.stepSize changed to ${stepSize.value}.`);
  }, [props.stepSize]);

  const handleOnChange = (_: Event, newNumber: number | number[]) => {
    // This will never be the case as we do not have a range slider. However, we should
    // make sure this is properly handled.
    if (Array.isArray(newNumber)) {
      newNumber = newNumber[0];
    }

    let serializedObject: SerializedObject;
    if (value.type === "Quantity") {
      serializedObject = {
        type: "Quantity",
        value: {
          magnitude: newNumber,
          unit: value.value.unit,
        } as QuantityMap,
        full_access_path: `${fullAccessPath}.value`,
        readonly: value.readonly,
        doc: docString,
      };
    } else {
      serializedObject = {
        type: value.type,
        value: newNumber,
        full_access_path: `${fullAccessPath}.value`,
        readonly: value.readonly,
        doc: docString,
      };
    }
    changeCallback(serializedObject);
  };

  const handleValueChange = (
    newValue: number,
    name: string,
    valueObject: NumberObject,
  ) => {
    let serializedObject: SerializedObject;
    if (valueObject.type === "Quantity") {
      serializedObject = {
        type: valueObject.type,
        value: {
          magnitude: newValue,
          unit: valueObject.value.unit,
        } as QuantityMap,
        full_access_path: `${fullAccessPath}.${name}`,
        readonly: valueObject.readonly,
        doc: null,
      };
    } else {
      serializedObject = {
        type: valueObject.type,
        value: newValue,
        full_access_path: `${fullAccessPath}.${name}`,
        readonly: valueObject.readonly,
        doc: null,
      };
    }
    changeCallback(serializedObject);
  };

  const deconstructNumberDict = (
    numberDict: NumberObject,
  ): [number, boolean, string | undefined] => {
    let numberMagnitude = 0;
    let numberUnit: string | undefined = undefined;
    const numberReadOnly = numberDict.readonly;

    if (numberDict.type === "int" || numberDict.type === "float") {
      numberMagnitude = numberDict.value;
    } else if (numberDict.type === "Quantity") {
      numberMagnitude = numberDict.value.magnitude;
      numberUnit = numberDict.value.unit;
    }

    return [numberMagnitude, numberReadOnly, numberUnit];
  };

  const [valueMagnitude, valueReadOnly, valueUnit] = deconstructNumberDict(value);
  const [minMagnitude, minReadOnly] = deconstructNumberDict(min);
  const [maxMagnitude, maxReadOnly] = deconstructNumberDict(max);
  const [stepSizeMagnitude, stepSizeReadOnly] = deconstructNumberDict(stepSize);

  return (
    <div className="component sliderComponent" id={id}>
      {process.env.NODE_ENV === "development" && (
        <div>Render count: {renderCount.current}</div>
      )}

      <Row>
        <Col xs="auto" xl="auto">
          <InputGroup.Text>
            {displayName}
            <DocStringComponent docString={docString} />
          </InputGroup.Text>
        </Col>
        <Col xs="5" xl>
          <Slider
            style={{ margin: "0px 0px 10px 0px" }}
            aria-label="Always visible"
            // valueLabelDisplay="on"
            disabled={valueReadOnly}
            value={valueMagnitude}
            onChange={(event, newNumber) => handleOnChange(event, newNumber)}
            min={minMagnitude}
            max={maxMagnitude}
            step={stepSizeMagnitude}
            marks={[
              { value: minMagnitude, label: `${minMagnitude}` },
              { value: maxMagnitude, label: `${maxMagnitude}` },
            ]}
          />
        </Col>
        <Col xs="3" xl>
          <NumberComponent
            isInstantUpdate={isInstantUpdate}
            fullAccessPath={`${fullAccessPath}.value`}
            docString={docString}
            readOnly={valueReadOnly}
            type={value.type}
            value={valueMagnitude}
            unit={valueUnit}
            addNotification={() => {}}
            changeCallback={changeCallback}
            id={id + "-value"}
          />
        </Col>
        <Col xs="auto">
          <ToggleButton
            id={`button-${id}`}
            onClick={() => setOpen(!open)}
            type="checkbox"
            checked={open}
            value=""
            className="btn"
            variant="light"
            aria-controls="slider-settings"
            aria-expanded={open}>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              className="bi bi-gear"
              viewBox="0 0 16 16">
              <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z" />
              <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115l.094-.319z" />
            </svg>
          </ToggleButton>
        </Col>
      </Row>
      <Collapse in={open}>
        <Form.Group>
          <Row
            className="justify-content-center"
            style={{ paddingTop: "20px", margin: "10px" }}>
            <Col xs="auto">
              <Form.Label>Min Value</Form.Label>
              <Form.Control
                type="number"
                value={minMagnitude}
                disabled={minReadOnly}
                onChange={(e) => handleValueChange(Number(e.target.value), "min", min)}
              />
            </Col>

            <Col xs="auto">
              <Form.Label>Max Value</Form.Label>
              <Form.Control
                type="number"
                value={maxMagnitude}
                disabled={maxReadOnly}
                onChange={(e) => handleValueChange(Number(e.target.value), "max", max)}
              />
            </Col>

            <Col xs="auto">
              <Form.Label>Step Size</Form.Label>
              <Form.Control
                type="number"
                value={stepSizeMagnitude}
                disabled={stepSizeReadOnly}
                onChange={(e) =>
                  handleValueChange(Number(e.target.value), "step_size", stepSize)
                }
              />
            </Col>
          </Row>
        </Form.Group>
      </Collapse>
    </div>
  );
});

SliderComponent.displayName = "SliderComponent";
