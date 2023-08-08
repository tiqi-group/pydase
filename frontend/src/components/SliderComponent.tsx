import React, { useEffect, useRef, useState } from 'react';
import { InputGroup, Form, Row, Col, Button, Collapse } from 'react-bootstrap';
import { emit_update } from '../socket';
import { DocStringComponent } from './DocStringComponent';
import { Slider } from '@mui/material';
import { NumberComponent } from './NumberComponent';

interface SliderComponentProps {
  name: string;
  min: number;
  max: number;
  parent_path?: string;
  value: number;
  readOnly: boolean;
  docString: string;
  stepSize: number;
  isInstantUpdate: boolean;
}

export const SliderComponent = React.memo((props: SliderComponentProps) => {
  const renderCount = useRef(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    renderCount.current++;
  });

  const {
    name,
    parent_path,
    value,
    min,
    max,
    stepSize,
    readOnly,
    docString,
    isInstantUpdate
  } = props;

  const emitSliderUpdate = (
    name: string,
    parent_path: string,
    value: number,
    callback?: (ack: unknown) => void,
    min: number = props.min,
    max: number = props.max,
    stepSize: number = props.stepSize
  ) => {
    emit_update(
      name,
      parent_path,
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
    emitSliderUpdate(name, parent_path, newNumber);
  };

  const handleValueChange = (newValue: number, valueType: string) => {
    switch (valueType) {
      case 'min':
        emitSliderUpdate(name, parent_path, value, undefined, newValue);
        break;
      case 'max':
        emitSliderUpdate(name, parent_path, value, undefined, min, newValue);
        break;
      case 'stepSize':
        emitSliderUpdate(name, parent_path, value, undefined, min, max, newValue);
        break;
      default:
        break;
    }
  };

  return (
    <div className="sliderComponent" id={parent_path.concat('.' + name)}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}

      <DocStringComponent docString={docString} />
      <Row>
        <Col xs="auto">
          <InputGroup.Text>{name}</InputGroup.Text>
        </Col>
        <Col xs="5">
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
        <Col xs={4}>
          <NumberComponent
            isInstantUpdate={isInstantUpdate}
            parent_path={parent_path}
            name={name}
            docString=""
            readOnly={readOnly}
            type="float"
            value={value}
            showName={false}
            customEmitUpdate={emitSliderUpdate}
          />
        </Col>
      </Row>
      <Row xs="auto">
        <Button
          onClick={() => setOpen(!open)}
          aria-controls="slider-settings"
          aria-expanded={open}>
          Settings
        </Button>
        <Collapse in={open}>
          <div id="slider-settings">
            <Form.Group>
              <Form.Label>Min Value</Form.Label>
              <Form.Control
                type="number"
                value={min}
                onChange={(e) => handleValueChange(Number(e.target.value), 'min')}
              />

              <Form.Label>Max Value</Form.Label>
              <Form.Control
                type="number"
                value={max}
                onChange={(e) => handleValueChange(Number(e.target.value), 'max')}
              />

              <Form.Label>Step Size</Form.Label>
              <Form.Control
                type="number"
                value={stepSize}
                onChange={(e) => handleValueChange(Number(e.target.value), 'stepSize')}
              />
            </Form.Group>
          </div>
        </Collapse>
      </Row>
    </div>
  );
});
