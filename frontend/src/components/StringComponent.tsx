import React, { useEffect, useRef, useState } from 'react';
import { Form, InputGroup } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import '../App.css';
import { LevelName } from './NotificationsComponent';

// TODO: add button functionality

type StringComponentProps = {
  name: string;
  parentPath?: string;
  value: string;
  readOnly: boolean;
  docString: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (
    value: unknown,
    attributeName?: string,
    prefix?: string,
    callback?: (ack: unknown) => void
  ) => void;
  displayName: string;
  id: string;
};

export const StringComponent = React.memo((props: StringComponentProps) => {
  const {
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
  const fullAccessPath = [props.parentPath, props.name]
    .filter((element) => element)
    .join('.');

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
      changeCallback(event.target.value);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !isInstantUpdate) {
      changeCallback(inputString);
    }
  };

  const handleBlur = () => {
    if (!isInstantUpdate) {
      changeCallback(inputString);
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
