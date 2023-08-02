import React, { useEffect, useRef, useState } from 'react';
import { InputGroup, Form, Row, Col, Button, Collapse } from 'react-bootstrap';
import { emit_update } from '../socket';
import { DocStringComponent } from './DocStringComponent';
import { Slider } from '@mui/material';

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

  const { name, parent_path, value, min, max, stepSize, readOnly, docString } = props;

  const socketEmit = (
    newNumber: number,
    min: number = props.min,
    max: number = props.max,
    stepSize: number = props.stepSize
  ) => {
    emit_update(name, parent_path, {
      value: newNumber,
      min: min,
      max: max,
      step_size: stepSize
    });
  };
  const handleOnChange = (event, newNumber: number | number[]) => {
    // This will never be the case as we do not have a range slider. However, we should
    // make sure this is properly handled.
    if (Array.isArray(newNumber)) {
      newNumber = newNumber[0];
    }
    socketEmit(newNumber, min, max, stepSize);
  };

  const handleValueChange = (newValue: number, valueType: string) => {
    switch (valueType) {
      case 'min':
        socketEmit(value, newValue, max, stepSize);
        break;
      case 'max':
        socketEmit(value, min, newValue, stepSize);
        break;
      case 'stepSize':
        socketEmit(value, min, max, newValue);
        break;
      default:
        break;
    }
  };

  return (
    <div className={'slider'} id={parent_path.concat('.' + name)}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}

      <DocStringComponent docString={docString} />
      <Row>
        <Col className="col-5 d-flex align-items-center">
          <InputGroup.Text
          // style={{ height: '80px' }}
          >
            {name}
          </InputGroup.Text>
          {/* <Form.Group> */}
          <Slider
            style={{ flex: 1, margin: '0px 0px 5px 10px' }}
            aria-label="Always visible"
            valueLabelDisplay="on"
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
          {/* <Form.Control
              type="text"
              value={value}
              name={name}
              disabled={true}
              style={{ flex: 1, margin: '5px 0px 0px 10px' }}
            /> */}
          {/* </Form.Group> */}
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
