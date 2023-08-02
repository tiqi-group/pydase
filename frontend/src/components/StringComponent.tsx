import React, { useEffect, useRef, useState } from 'react';
import { Form, InputGroup } from 'react-bootstrap';
import { emit_update } from '../socket';
import { DocStringComponent } from './DocStringComponent';

// TODO: add button functionality

interface StringComponentProps {
  name: string;
  parent_path?: string;
  value: string;
  readOnly: boolean;
  docString: string;
  isInstantUpdate: boolean;
}

export const StringComponent = React.memo((props: StringComponentProps) => {
  const renderCount = useRef(0);
  const [inputString, setInputString] = useState(props.value);

  const { name, parent_path, readOnly, docString, isInstantUpdate } = props;
  useEffect(() => {
    renderCount.current++;
    if (isInstantUpdate && props.value !== inputString) {
      setInputString(props.value);
    }
  }, [isInstantUpdate, props.value, inputString, renderCount]);

  const handleChange = (event) => {
    setInputString(event.target.value);
    if (isInstantUpdate) {
      emit_update(name, parent_path, event.target.value);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !isInstantUpdate) {
      emit_update(name, parent_path, inputString);
    }
  };

  const handleBlur = () => {
    if (!isInstantUpdate) {
      emit_update(name, parent_path, inputString);
    }
  };

  return (
    <div className={'component boolean'} id={parent_path.concat(name)}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}
      <DocStringComponent docString={docString} />
      <div className="row">
        <div className="col-5 d-flex">
          <InputGroup>
            <InputGroup.Text>{name}</InputGroup.Text>
            <Form.Control
              type="text"
              value={inputString}
              disabled={readOnly}
              name={name}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              onBlur={handleBlur}
            />
          </InputGroup>
        </div>
      </div>
    </div>
  );
});
