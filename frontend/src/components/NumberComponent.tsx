import React, { useEffect, useRef, useState } from 'react';
import {
  OverlayTrigger,
  Badge,
  Tooltip,
  Form,
  InputGroup,
  Button
} from 'react-bootstrap';
import { socket } from '../socket';
import { DocStringComponent } from './DocStringComponent';

// TODO: add button functionality

interface ButtonComponentProps {
  name: string;
  parent_path?: string;
  value: number;
  readOnly: boolean;
  docString: string;
}

const handleNumericKey = (key: string, value: string, selectionStart: number) => {
  // Check if a number key or a decimal point key is pressed
  if (key === '.' && value.includes('.')) {
    // Check if value already contains a decimal. If so, ignore input.
    // eslint-disable-next-line no-console
    console.warn('Number already contains decimal! Ignoring...');
    return { value, selectionStart };
  }
  // Add the new key at the cursor's position
  const newValue = value.slice(0, selectionStart) + key + value.slice(selectionStart);
  return { value: newValue, selectionStart: selectionStart + 1 };
};

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

export const NumberComponent = React.memo((props: ButtonComponentProps) => {
  const renderCount = useRef(0);
  // Create a state for the cursor position
  const [cursorPosition, setCursorPosition] = useState(null);
  // Create a state for the input string
  const [inputString, setInputString] = useState(props.value.toString());

  useEffect(() => {
    renderCount.current++;

    // Set the cursor position and input string after the component re-renders
    const inputElement = document.getElementsByName(name)[0] as HTMLInputElement;
    if (inputElement && cursorPosition !== null) {
      // Setting input string as trailing zeros after the decimal will be stripped
      // otherwise
      inputElement.value = inputString;

      inputElement.setSelectionRange(cursorPosition, cursorPosition);
    }
  });

  const { name, parent_path, value, readOnly, docString } = props;

  const handleKeyDown = (event) => {
    const { key, target } = event;
    if (key === 'F5' || key === 'ArrowRight' || key === 'ArrowLeft') {
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
        selectionStart
      ));
    } else if (key === '.') {
      ({ value: newValue, selectionStart } = handleNumericKey(
        key,
        value,
        selectionStart
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
    } else {
      console.debug(key);
      return;
    }

    // Update the input value and maintain the cursor position
    socket.emit('frontend_update', {
      name: name,
      value: Number(newValue)
    });

    setInputString(newValue);

    // Save the current cursor position before the component re-renders
    setCursorPosition(selectionStart);
  };

  return (
    <div className={'component boolean'} id={parent_path.concat(name)}>
      <p>Render count: {renderCount.current}</p>
      <DocStringComponent docString={docString} />
      <div className="row">
        <div className="col-5 d-flex">
          <InputGroup>
            <InputGroup.Text>{name}</InputGroup.Text>
            <Form.Control
              type="text"
              value={value}
              readOnly={readOnly}
              name={name}
              onKeyDown={handleKeyDown}
            />
          </InputGroup>
          <div className="d-flex flex-column">
            <Button
              style={{ padding: '0.2em 6px', fontSize: '0.70rem' }}
              // className="mb-1"
              variant="outline-secondary">
              +
            </Button>
            <Button
              style={{ padding: '0.2em 6px', fontSize: '0.70rem' }}
              variant="outline-secondary">
              -
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
});
