import React, { useEffect, useRef, useState } from 'react';
import { InputGroup, Form, Row, Col, Collapse, ToggleButton } from 'react-bootstrap';
import { emit_update } from '../socket';
import { DocStringComponent } from './DocStringComponent';
import { Slider } from '@mui/material';
import { NumberComponent } from './NumberComponent';
import { getIdFromFullAccessPath } from '../utils/stringUtils';

interface SliderComponentProps {
  name: string;
  min: number;
  max: number;
  parentPath?: string;
  value: number;
  readOnly: boolean;
  docString: string;
  stepSize: number;
  isInstantUpdate: boolean;
  addNotification: (message: string) => void;
}

export const SliderComponent = React.memo((props: SliderComponentProps) => {
  const renderCount = useRef(0);
  const [open, setOpen] = useState(false);
  const {
    name,
    parentPath,
    value,
    min,
    max,
    stepSize,
    readOnly,
    docString,
    isInstantUpdate,
    addNotification
  } = props;
  const fullAccessPath = parentPath.concat('.' + name);
  const id = getIdFromFullAccessPath(fullAccessPath);

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${parentPath}.${name} changed to ${value}.`);
  }, [props.value]);

  useEffect(() => {
    addNotification(`${parentPath}.${name}.min changed to ${min}.`);
  }, [props.min]);

  useEffect(() => {
    addNotification(`${parentPath}.${name}.max changed to ${max}.`);
  }, [props.max]);

  useEffect(() => {
    addNotification(`${parentPath}.${name}.stepSize changed to ${stepSize}.`);
  }, [props.stepSize]);

  const emitSliderUpdate = (
    name: string,
    parentPath: string,
    value: number,
    callback?: (ack: unknown) => void,
    min: number = props.min,
    max: number = props.max,
    stepSize: number = props.stepSize
  ) => {
    emit_update(
      name,
      parentPath,
      {
        value: value,
        min: min,
        max: max,
        step_size: stepSize
      },
      callback
    );
  };
  const handleOnChange = (event, newNumber: number | number[]) => {
    // This will never be the case as we do not have a range slider. However, we should
    // make sure this is properly handled.
    if (Array.isArray(newNumber)) {
      newNumber = newNumber[0];
    }
    emitSliderUpdate(name, parentPath, newNumber);
  };

  const handleValueChange = (newValue: number, valueType: string) => {
    switch (valueType) {
      case 'min':
        emitSliderUpdate(name, parentPath, value, undefined, newValue);
        break;
      case 'max':
        emitSliderUpdate(name, parentPath, value, undefined, min, newValue);
        break;
      case 'stepSize':
        emitSliderUpdate(name, parentPath, value, undefined, min, max, newValue);
        break;
      default:
        break;
    }
  };

  return (
    <div className="sliderComponent" id={id}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}

      <DocStringComponent docString={docString} />
      <Row>
        <Col xs="auto" xl="auto">
          <InputGroup.Text>{name}</InputGroup.Text>
        </Col>
        <Col xs="5" xl>
          <Slider
            style={{ margin: '0px 0px 10px 0px' }}
            aria-label="Always visible"
            // valueLabelDisplay="on"
            disabled={readOnly}
            value={value}
            onChange={(event, newNumber) => handleOnChange(event, newNumber)}
            min={min}
            max={max}
            step={stepSize}
            marks={[
              { value: min, label: `${min}` },
              { value: max, label: `${max}` }
            ]}
          />
        </Col>
        <Col xs="3" xl>
          <NumberComponent
            isInstantUpdate={isInstantUpdate}
            parentPath={parentPath}
            name={name}
            docString=""
            readOnly={readOnly}
            type="float"
            value={value}
            showName={false}
            customEmitUpdate={emitSliderUpdate}
            addNotification={() => null}
          />
        </Col>
        <Col xs="auto">
          <ToggleButton
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
            style={{ paddingTop: '20px', margin: '10px' }}>
            <Col xs="auto">
              <Form.Label>Min Value</Form.Label>
              <Form.Control
                type="number"
                value={min}
                onChange={(e) => handleValueChange(Number(e.target.value), 'min')}
              />
            </Col>

            <Col xs="auto">
              <Form.Label>Max Value</Form.Label>
              <Form.Control
                type="number"
                value={max}
                onChange={(e) => handleValueChange(Number(e.target.value), 'max')}
              />
            </Col>

            <Col xs="auto">
              <Form.Label>Step Size</Form.Label>
              <Form.Control
                type="number"
                value={stepSize}
                onChange={(e) => handleValueChange(Number(e.target.value), 'stepSize')}
              />
            </Col>
          </Row>
        </Form.Group>
      </Collapse>
    </div>
  );
});
