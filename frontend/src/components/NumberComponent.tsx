import React, { useEffect, useRef, useState } from 'react';
import { Form, InputGroup, Button } from 'react-bootstrap';
import { emit_update } from '../socket';
import { DocStringComponent } from './DocStringComponent';
import '../App.css';

// TODO: add button functionality

interface NumberComponentProps {
  name: string;
  type: 'float' | 'int';
  parentPath?: string;
  value: number;
  readOnly: boolean;
  docString: string;
  isInstantUpdate: boolean;
  unit?: string;
  showName?: boolean;
  customEmitUpdate?: (
    name: string,
    parent_path: string,
    value: number,
    callback?: (ack: unknown) => void
  ) => void;
  addNotification: (string) => void;
}

// TODO: highlight the digit that is being changed by setting both selectionStart and
// selectionEnd
const handleArrowKey = (
  key: string,
  value: string,
  selectionStart: number,
  selectionEnd: number
) => {
  // Split the input value into the integer part and decimal part
  const parts = value.split('.');
  const beforeDecimalCount = parts[0].length; // Count digits before the decimal
  const afterDecimalCount = parts[1] ? parts[1].length : 0; // Count digits after the decimal

  const isCursorAfterDecimal = selectionStart > beforeDecimalCount;

  // Calculate the increment/decrement value based on the cursor position
  let increment = 0;
  if (isCursorAfterDecimal) {
    increment = Math.pow(10, beforeDecimalCount + 1 - selectionStart);
  } else {
    increment = Math.pow(10, beforeDecimalCount - selectionStart);
  }

  // Convert the input value to a number, increment or decrement it based on the
  // arrow key
  const numValue = parseFloat(value) + (key === 'ArrowUp' ? increment : -increment);

  // Convert the resulting number to a string, maintaining the same number of digits
  // after the decimal
  const newValue = numValue.toFixed(afterDecimalCount);

  // Check if the length of the integer part of the number string has in-/decreased
  const newBeforeDecimalCount = newValue.split('.')[0].length;
  if (newBeforeDecimalCount > beforeDecimalCount) {
    // Move the cursor one position to the right
    selectionStart += 1;
  } else if (newBeforeDecimalCount < beforeDecimalCount) {
    // Move the cursor one position to the left
    selectionStart -= 1;
  }
  return { value: newValue, selectionStart };
};

const handleBackspaceKey = (
  value: string,
  selectionStart: number,
  selectionEnd: number
) => {
  if (selectionEnd > selectionStart) {
    // If there is a selection, delete all characters in the selection
    return {
      value: value.slice(0, selectionStart) + value.slice(selectionEnd),
      selectionStart
    };
  } else if (selectionStart > 0) {
    return {
      value: value.slice(0, selectionStart - 1) + value.slice(selectionStart),
      selectionStart: selectionStart - 1
    };
  }
  return { value, selectionStart };
};

const handleDeleteKey = (
  value: string,
  selectionStart: number,
  selectionEnd: number
) => {
  if (selectionEnd > selectionStart) {
    // If there is a selection, delete all characters in the selection
    return {
      value: value.slice(0, selectionStart) + value.slice(selectionEnd),
      selectionStart
    };
  } else if (selectionStart < value.length) {
    return {
      value: value.slice(0, selectionStart) + value.slice(selectionStart + 1),
      selectionStart
    };
  }
  return { value, selectionStart };
};

export const NumberComponent = React.memo((props: NumberComponentProps) => {
  const {
    name,
    parentPath,
    readOnly,
    docString,
    isInstantUpdate,
    unit,
    addNotification
  } = props;

  // Whether to show the name infront of the component (false if used with a slider)
  const showName = props.showName !== undefined ? props.showName : true;
  // If emitUpdate is passed, use this instead of the emit_update from the socket
  // Also used when used with a slider
  const emitUpdate =
    props.customEmitUpdate !== undefined ? props.customEmitUpdate : emit_update;

  const renderCount = useRef(0);
  // Create a state for the cursor position
  const [cursorPosition, setCursorPosition] = useState(null);
  // Create a state for the input string
  const [inputString, setInputString] = useState(props.value.toString());

  useEffect(() => {
    renderCount.current++;

    // Set the cursor position after the component re-renders
    const inputElement = document.getElementsByName(
      parentPath.concat(name)
    )[0] as HTMLInputElement;
    if (inputElement && cursorPosition !== null) {
      inputElement.setSelectionRange(cursorPosition, cursorPosition);
    }
  });

  useEffect(() => {
    // Parse the input string to a number for comparison
    const numericInputString =
      props.type === 'int' ? parseInt(inputString) : parseFloat(inputString);
    // Only update the inputString if it's different from the prop value
    if (props.value !== numericInputString) {
      setInputString(props.value.toString());
    }

    // emitting notification
    let notificationMsg = `${parentPath}.${name} changed to ${props.value}`;
    if (unit === undefined) {
      notificationMsg += '.';
    } else {
      notificationMsg += ` ${unit}.`;
    }
    addNotification(notificationMsg);
  }, [props.value]);

  const handleNumericKey = (
    key: string,
    value: string,
    selectionStart: number,
    selectionEnd: number
  ) => {
    // Check if a number key or a decimal point key is pressed
    if (key === '.' && (value.includes('.') || props.type === 'int')) {
      // Check if value already contains a decimal. If so, ignore input.
      // eslint-disable-next-line no-console
      console.warn('Invalid input! Ignoring...');
      return { value, selectionStart };
    }

    let newValue = value;

    // Add the new key at the cursor's position
    if (selectionEnd > selectionStart) {
      // If there is a selection, replace it with the key
      newValue = value.slice(0, selectionStart) + key + value.slice(selectionEnd);
    } else {
      // otherwise, append the key after the selection start
      newValue = value.slice(0, selectionStart) + key + value.slice(selectionStart);
    }

    return { value: newValue, selectionStart: selectionStart + 1 };
  };
  const handleKeyDown = (event) => {
    const { key, target } = event;
    if (
      key === 'F1' ||
      key === 'F5' ||
      key === 'F12' ||
      key === 'Tab' ||
      key === 'ArrowRight' ||
      key === 'ArrowLeft'
    ) {
      return;
    }
    event.preventDefault();

    // Get the current input value and cursor position
    const { value } = target;
    let { selectionStart } = target;
    const { selectionEnd } = target;

    let newValue: string = value;
    if (event.ctrlKey && key === 'a') {
      // Select everything when pressing Ctrl + a
      target.setSelectionRange(0, target.value.length);
      return;
    } else if (!isNaN(key) && key !== ' ') {
      // Check if a number key or a decimal point key is pressed
      ({ value: newValue, selectionStart } = handleNumericKey(
        key,
        value,
        selectionStart,
        selectionEnd
      ));
    } else if (key === '.') {
      ({ value: newValue, selectionStart } = handleNumericKey(
        key,
        value,
        selectionStart,
        selectionEnd
      ));
    } else if (key === 'ArrowUp' || key === 'ArrowDown') {
      ({ value: newValue, selectionStart } = handleArrowKey(
        key,
        value,
        selectionStart,
        selectionEnd
      ));
    } else if (key === 'Backspace') {
      ({ value: newValue, selectionStart } = handleBackspaceKey(
        value,
        selectionStart,
        selectionEnd
      ));
    } else if (key === 'Delete') {
      ({ value: newValue, selectionStart } = handleDeleteKey(
        value,
        selectionStart,
        selectionEnd
      ));
    } else if (key === 'Enter' && !isInstantUpdate) {
      emitUpdate(name, parentPath, Number(newValue));
      return;
    } else {
      console.debug(key);
      return;
    }

    // Update the input value and maintain the cursor position
    if (isInstantUpdate) {
      emitUpdate(name, parentPath, Number(newValue));
    }

    setInputString(newValue);

    // Save the current cursor position before the component re-renders
    setCursorPosition(selectionStart);
  };

  const handleClick = (event, action: 'plus' | 'minus') => {
    const keyAction = action == 'plus' ? 'ArrowUp' : 'ArrowDown';
    const { value: newValue } = handleArrowKey(
      keyAction,
      inputString,
      inputString.length,
      inputString.length
    );

    emitUpdate(name, parentPath, Number(newValue));

    setInputString(newValue);
  };

  const handleBlur = () => {
    if (!isInstantUpdate) {
      // If not in "instant update" mode, emit an update when the input field loses focus
      emitUpdate(name, parentPath, Number(inputString));
    }
  };

  return (
    <div className="numberComponent" id={parentPath.concat('.' + name)}>
      {process.env.NODE_ENV === 'development' && showName && (
        <p>Render count: {renderCount.current}</p>
      )}
      <DocStringComponent docString={docString} />
      <div className="d-flex">
        <InputGroup>
          {showName && <InputGroup.Text>{name}</InputGroup.Text>}
          <Form.Control
            type="text"
            value={inputString}
            disabled={readOnly}
            name={parentPath.concat(name)}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            className={isInstantUpdate && !readOnly ? 'instantUpdate' : ''}
          />
          {unit && <InputGroup.Text>{unit}</InputGroup.Text>}
        </InputGroup>
        {!readOnly && (
          <div className="d-flex flex-column">
            <Button
              className="numberComponentButton"
              variant="outline-secondary"
              onClick={(event) => handleClick(event, 'plus')}>
              +
            </Button>
            <Button
              className="numberComponentButton"
              variant="outline-secondary"
              onClick={(event) => handleClick(event, 'minus')}>
              -
            </Button>
          </div>
        )}
      </div>
    </div>
  );
});
