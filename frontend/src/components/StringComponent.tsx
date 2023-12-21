import React, { useEffect, useRef, useState } from 'react';
import { Form, InputGroup } from 'react-bootstrap';
import { setAttribute } from '../socket';
import { DocStringComponent } from './DocStringComponent';
import '../App.css';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { LevelName } from './NotificationsComponent';

// TODO: add button functionality

interface StringComponentProps {
  name: string;
  parentPath?: string;
  value: string;
  readOnly: boolean;
  docString: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
}

export const StringComponent = React.memo((props: StringComponentProps) => {
  const { name, parentPath, readOnly, docString, isInstantUpdate, addNotification } =
    props;

  const renderCount = useRef(0);
  const [inputString, setInputString] = useState(props.value);
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');
  const id = getIdFromFullAccessPath(fullAccessPath);

  useEffect(() => {
    renderCount.current++;
  }, [isInstantUpdate, inputString, renderCount]);

  useEffect(() => {
    // Only update the inputString if it's different from the prop value
    if (props.value !== inputString) {
      setInputString(props.value);
    }
    addNotification(`${parentPath}.${name} changed to ${props.value}.`);
  }, [props.value]);

  const handleChange = (event) => {
    setInputString(event.target.value);
    if (isInstantUpdate) {
      setAttribute(name, parentPath, event.target.value);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !isInstantUpdate) {
      setAttribute(name, parentPath, inputString);
    }
  };

  const handleBlur = () => {
    if (!isInstantUpdate) {
      setAttribute(name, parentPath, inputString);
    }
  };

  return (
    <div className={'stringComponent'} id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <DocStringComponent docString={docString} />
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
          className={isInstantUpdate && !readOnly ? 'instantUpdate' : ''}
        />
      </InputGroup>
    </div>
  );
});
