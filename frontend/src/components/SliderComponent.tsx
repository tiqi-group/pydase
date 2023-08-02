import React, { useEffect, useRef, useState } from 'react';
import {
  OverlayTrigger,
  Badge,
  Tooltip,
  InputGroup,
  Form,
  Row,
  Col,
  Button,
  Collapse
} from 'react-bootstrap';
import { socket } from '../socket';
import RangeSlider from 'react-bootstrap-range-slider';
import { DocStringComponent } from './DocStringComponent';

interface SliderComponentProps {
  name: string;
  min: number;
  max: number;
  parent_path?: string;
  value: number;
  readOnly: boolean;
  docString: string;
  stepSize: number;
}

export const SliderComponent = React.memo((props: SliderComponentProps) => {
  const renderCount = useRef(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    renderCount.current++;
  });

  const { name, parent_path, value, readOnly, docString } = props;
  const [min, setMin] = useState(props.min);
  const [max, setMax] = useState(props.max);
  const [stepSize, setStepSize] = useState(props.stepSize);

  const socketEmit = (
    newNumber: number,
    min: number = props.min,
    max: number = props.max,
    stepSize: number = props.stepSize
  ) => {
    socket.emit('frontend_update', {
      name: name,
      value: { value: newNumber, min: min, max: max, step_size: stepSize }
    });
  };
  const handleOnChange = (event, newNumber: number) => {
    socketEmit(newNumber, min, max, stepSize);
  };

  const handleValueChange = (newValue: number, valueType: string) => {
    switch (valueType) {
      case 'min':
        setMin(newValue);
        break;
      case 'max':
        setMax(newValue);
        break;
      case 'stepSize':
        setStepSize(newValue);
        break;
      default:
        break;
    }
    socketEmit(value, min, max, stepSize);
  };

  return (
    <div className={'component boolean'} id={parent_path.concat('.' + name)}>
      <p>Render count: {renderCount.current}</p>

      <DocStringComponent docString={docString} />
      <Row>
        <Col className="col-2 d-flex align-items-center">
          <InputGroup.Text style={{ height: '65px' }}>{name}</InputGroup.Text>
          <Form.Group>
            <RangeSlider
              disabled={readOnly}
              value={value}
              onChange={(event, newNumber) => handleOnChange(event, newNumber)}
              min={min}
              max={max}
              step={stepSize}
              tooltip={'off'}
            />
            <Form.Control type="text" value={value} name={name} disabled={true} />
          </Form.Group>
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
