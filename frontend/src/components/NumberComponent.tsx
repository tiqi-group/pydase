import React, { useEffect, useState, useRef } from 'react';
import { Form, InputGroup } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import '../App.css';
import { LevelName } from './NotificationsComponent';
import { SerializedValue } from './GenericComponent';

// TODO: add button functionality

export type QuantityObject = {
  type: 'Quantity';
  readonly: boolean;
  value: {
    magnitude: number;
    unit: string;
  };
  doc?: string;
};
export type IntObject = {
  type: 'int';
  readonly: boolean;
  value: number;
  doc?: string;
};
export type FloatObject = {
  type: 'float';
  readonly: boolean;
  value: number;
  doc?: string;
};
export type NumberObject = IntObject | FloatObject | QuantityObject;

type NumberComponentProps = {
  type: 'float' | 'int' | 'Quantity';
  fullAccessPath: string;
  value: number;
  readOnly: boolean;
  docString: string;
  isInstantUpdate: boolean;
  unit?: string;
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (value: SerializedValue, callback?: (ack: unknown) => void) => void;
  displayName?: string;
  id: string;
};

// TODO: highlight the digit that is being changed by setting both selectionStart and
// selectionEnd
const handleArrowKey = (
  key: string,
  value: string,
  selectionStart: number
  // selectionEnd: number
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

const handleNumericKey = (
  key: string,
  value: string,
  selectionStart: number,
  selectionEnd: number
) => {
  // Check if a number key or a decimal point key is pressed
  if (key === '.' && value.includes('.')) {
    // Check if value already contains a decimal. If so, ignore input.
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

export const NumberComponent = React.memo((props: NumberComponentProps) => {
  const {
    fullAccessPath,
    value,
    readOnly,
    type,
    docString,
    isInstantUpdate,
    unit,
    addNotification,
    changeCallback = () => {},
    displayName,
    id
  } = props;

  // Create a state for the cursor position
  const [cursorPosition, setCursorPosition] = useState(null);
  // Create a state for the input string
  const [inputString, setInputString] = useState(value.toString());
  const renderCount = useRef(0);

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
    } else if (key === '-') {
      if (selectionStart === 0 && !value.startsWith('-')) {
        newValue = '-' + value;
        selectionStart++;
      } else if (value.startsWith('-') && selectionStart === 1) {
        newValue = value.substring(1); // remove minus sign
        selectionStart--;
      } else {
        return; // Ignore "-" pressed in other positions
      }
    } else if (!isNaN(key) && key !== ' ') {
      // Check if a number key or a decimal point key is pressed
      ({ value: newValue, selectionStart } = handleNumericKey(
        key,
        value,
        selectionStart,
        selectionEnd
      ));
    } else if (key === '.' && (type === 'float' || type === 'Quantity')) {
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
        selectionStart
        // selectionEnd
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
      let updatedValue: number | Record<string, unknown> = Number(newValue);
      if (type === 'Quantity') {
        updatedValue = {
          magnitude: Number(newValue),
          unit: unit
        };
      }
      changeCallback({
        type: type,
        value: updatedValue,
        full_access_path: fullAccessPath,
        readonly: readOnly,
        doc: docString
      });
      return;
    } else {
      console.debug(key);
      return;
    }

    // Update the input value and maintain the cursor position
    if (isInstantUpdate) {
      let updatedValue: number | Record<string, unknown> = Number(newValue);
      if (type === 'Quantity') {
        updatedValue = {
          magnitude: Number(newValue),
          unit: unit
        };
      }
      changeCallback({
        type: type,
        value: updatedValue,
        full_access_path: fullAccessPath,
        readonly: readOnly,
        doc: docString
      });
    }

    setInputString(newValue);

    // Save the current cursor position before the component re-renders
    setCursorPosition(selectionStart);
  };

  const handleBlur = () => {
    if (!isInstantUpdate) {
      // If not in "instant update" mode, emit an update when the input field loses focus
      let updatedValue: number | Record<string, unknown> = Number(inputString);
      if (type === 'Quantity') {
        updatedValue = {
          magnitude: Number(inputString),
          unit: unit
        };
      }
      changeCallback({
        type: type,
        value: updatedValue,
        full_access_path: fullAccessPath,
        readonly: readOnly,
        doc: docString
      });
    }
  };
  useEffect(() => {
    // Parse the input string to a number for comparison
    const numericInputString =
      type === 'int' ? parseInt(inputString) : parseFloat(inputString);
    // Only update the inputString if it's different from the prop value
    if (value !== numericInputString) {
      setInputString(value.toString());
    }

    // emitting notification
    let notificationMsg = `${fullAccessPath} changed to ${props.value}`;
    if (unit === undefined) {
      notificationMsg += '.';
    } else {
      notificationMsg += ` ${unit}.`;
    }
    addNotification(notificationMsg);
  }, [value]);

  useEffect(() => {
    // Set the cursor position after the component re-renders
    const inputElement = document.getElementsByName(
      fullAccessPath
    )[0] as HTMLInputElement;
    if (inputElement && cursorPosition !== null) {
      inputElement.setSelectionRange(cursorPosition, cursorPosition);
    }
  });

  return (
    <div className="component numberComponent" id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <InputGroup>
        {displayName && (
          <InputGroup.Text>
            {displayName}
            <DocStringComponent docString={docString} />
          </InputGroup.Text>
        )}
        <Form.Control
          type="text"
          value={inputString}
          disabled={readOnly}
          name={fullAccessPath}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          className={isInstantUpdate && !readOnly ? 'instantUpdate' : ''}
        />
        {unit && <InputGroup.Text>{unit}</InputGroup.Text>}
      </InputGroup>
    </div>
  );
});
