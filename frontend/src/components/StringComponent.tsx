import React, { useEffect, useRef, useState } from 'react';
import { Form, InputGroup } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import '../App.css';
import { LevelName } from './NotificationsComponent';
import { SerializedValue } from './GenericComponent';

// TODO: add button functionality

type StringComponentProps = {
  fullAccessPath: string;
  value: string;
  readOnly: boolean;
  docString: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (value: SerializedValue, callback?: (ack: unknown) => void) => void;
  displayName: string;
  id: string;
};

export const StringComponent = React.memo((props: StringComponentProps) => {
  const {
    fullAccessPath,
    readOnly,
    docString,
    isInstantUpdate,
    addNotification,
    changeCallback = () => {},
    displayName,
    id
  } = props;

  const renderCount = useRef(0);
  const [inputString, setInputString] = useState(props.value);

  useEffect(() => {
    renderCount.current++;
  }, [isInstantUpdate, inputString, renderCount]);

  useEffect(() => {
    // Only update the inputString if it's different from the prop value
    if (props.value !== inputString) {
      setInputString(props.value);
    }
    addNotification(`${fullAccessPath} changed to ${props.value}.`);
  }, [props.value]);

  const handleChange = (event) => {
    setInputString(event.target.value);
    if (isInstantUpdate) {
      changeCallback({
        type: 'str',
        value: event.target.value,
        full_access_path: fullAccessPath,
        readonly: readOnly,
        doc: docString
      });
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !isInstantUpdate) {
      changeCallback({
        type: 'str',
        value: inputString,
        full_access_path: fullAccessPath,
        readonly: readOnly,
        doc: docString
      });
      event.preventDefault();
    }
  };

  const handleBlur = () => {
    if (!isInstantUpdate) {
      changeCallback({
        type: 'str',
        value: inputString,
        full_access_path: fullAccessPath,
        readonly: readOnly,
        doc: docString
      });
    }
  };

  return (
    <div className="component stringComponent" id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <InputGroup>
        <InputGroup.Text>
          {displayName}
          <DocStringComponent docString={docString} />
        </InputGroup.Text>
        <Form.Control
          type="text"
          name={id}
          value={inputString}
          disabled={readOnly}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          className={isInstantUpdate && !readOnly ? 'instantUpdate' : ''}
        />
      </InputGroup>
    </div>
  );
});
