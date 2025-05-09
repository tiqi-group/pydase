import React, { useEffect, useRef, useState } from "react";
import { Form, InputGroup } from "react-bootstrap";
import { DocStringComponent } from "./DocStringComponent";
import "../App.css";
import { LevelName } from "./NotificationsComponent";
import { SerializedObject } from "../types/SerializedObject";
import { QuantityMap } from "../types/QuantityMap";
import useRenderCount from "../hooks/useRenderCount";

// TODO: add button functionality

export interface QuantityObject {
  type: "Quantity";
  readonly: boolean;
  value: QuantityMap;
  doc: string | null;
}
export interface IntObject {
  type: "int";
  readonly: boolean;
  value: number;
  doc: string | null;
}
export interface FloatObject {
  type: "float";
  readonly: boolean;
  value: number;
  doc: string | null;
}
export type NumberObject = IntObject | FloatObject | QuantityObject;

interface NumberComponentProps {
  type: "float" | "int" | "Quantity";
  fullAccessPath: string;
  value: number;
  readOnly: boolean;
  docString: string | null;
  isInstantUpdate: boolean;
  unit?: string;
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (value: SerializedObject, callback?: (ack: unknown) => void) => void;
  displayName?: string;
  id: string;
}

// TODO: highlight the digit that is being changed by setting both selectionStart and
// selectionEnd
const handleArrowKey = (
  key: string,
  value: string,
  selectionStart: number,
  // selectionEnd: number
) => {
  // Split the input value into the integer part and decimal part
  const parts = value.split(".");
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
  const numValue = parseFloat(value) + (key === "ArrowUp" ? increment : -increment);

  // Convert the resulting number to a string, maintaining the same number of digits
  // after the decimal
  const newValue = numValue.toFixed(afterDecimalCount);

  // Check if the length of the integer part of the number string has in-/decreased
  const newBeforeDecimalCount = newValue.split(".")[0].length;
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
  selectionEnd: number,
) => {
  if (selectionEnd > selectionStart) {
    // If there is a selection, delete all characters in the selection
    return {
      value: value.slice(0, selectionStart) + value.slice(selectionEnd),
      selectionStart,
    };
  } else if (selectionStart > 0) {
    return {
      value: value.slice(0, selectionStart - 1) + value.slice(selectionStart),
      selectionStart: selectionStart - 1,
    };
  }
  return { value, selectionStart };
};

const handleDeleteKey = (
  value: string,
  selectionStart: number,
  selectionEnd: number,
) => {
  if (selectionEnd > selectionStart) {
    // If there is a selection, delete all characters in the selection
    return {
      value: value.slice(0, selectionStart) + value.slice(selectionEnd),
      selectionStart,
    };
  } else if (selectionStart < value.length) {
    return {
      value: value.slice(0, selectionStart) + value.slice(selectionStart + 1),
      selectionStart,
    };
  }
  return { value, selectionStart };
};

const handleNumericKey = (
  key: string,
  value: string,
  selectionStart: number,
  selectionEnd: number,
) => {
  let newValue = value;

  // Check if a number key or a decimal point key is pressed
  if (key === "." && value.includes(".")) {
    // Check if value already contains a decimal. If so, ignore input.
    console.warn("Invalid input! Ignoring...");
    return { value, selectionStart };
  }

  // Handle minus sign input
  if (key === "-") {
    if (selectionStart === 0 && selectionEnd > selectionStart) {
      // Replace selection with minus if selection starts at 0
      newValue = "-" + value.slice(selectionEnd);
      selectionStart = 1;
    } else if (selectionStart === 0 && !value.startsWith("-")) {
      // Add minus at the beginning if it doesn't exist
      newValue = "-" + value;
      selectionStart = 1;
    } else if (
      (selectionStart === 0 || selectionStart === 1) &&
      value.startsWith("-")
    ) {
      // Remove minus if it exists
      newValue = value.slice(1);
      selectionStart = 0;
    }

    return { value: newValue, selectionStart };
  }

  // Add the new key at the cursor's position
  if (selectionEnd > selectionStart) {
    // If there is a selection, replace it with the key
    newValue = value.slice(0, selectionStart) + key + value.slice(selectionEnd);
  } else {
    // Otherwise, insert the key at the cursor position
    newValue = value.slice(0, selectionStart) + key + value.slice(selectionStart);
  }

  return { value: newValue, selectionStart: selectionStart + 1 };
};

/**
 * Calculates the new cursor position after moving left by a specified step size.
 *
 * @param cursorPosition - The current position of the cursor.
 * @param step - The number of positions to move left.
 * @returns The new cursor position, clamped to a minimum of 0.
 */
const getCursorLeftPosition = (cursorPosition: number, step: number): number => {
  return Math.max(0, cursorPosition - step);
};

/**
 * Calculates the new cursor position after moving right by a specified step size.
 *
 * @param cursorPosition - The current position of the cursor.
 * @param step - The number of positions to move right.
 * @param maxPosition - The maximum allowed cursor position (e.g., value.length).
 * @returns The new cursor position, clamped to a maximum of maxPosition.
 */
const getCursorRightPosition = (
  cursorPosition: number,
  step: number,
  maxPosition: number,
): number => {
  return Math.min(maxPosition, cursorPosition + step);
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
    id,
  } = props;

  // Create a state for the cursor position
  const cursorPositionRef = useRef<number | null>(null);

  // Create a state for the input string
  const [inputString, setInputString] = useState(value.toString());
  const renderCount = useRenderCount();

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    const { key, target } = event;

    const inputTarget = target as HTMLInputElement;

    // Get the current input value and cursor position
    const { value } = inputTarget;
    const valueLength = value.length;
    const selectionEnd = inputTarget.selectionEnd ?? 0;
    let selectionStart = inputTarget.selectionStart ?? 0;

    if (key === "F1" || key === "F5" || key === "F12" || key === "Tab") {
      return;
    } else if (key === "ArrowLeft" || key === "ArrowRight") {
      const hasSelection = selectionEnd > selectionStart;

      if (hasSelection && !event.shiftKey) {
        // Collapse selection: ArrowLeft -> start, ArrowRight -> end
        const collapseTo = key === "ArrowLeft" ? selectionStart : selectionEnd;
        cursorPositionRef.current = collapseTo;
      } else {
        // No selection or shift key is pressed, just move cursor by one
        const newSelectionStart =
          key === "ArrowLeft"
            ? getCursorLeftPosition(selectionStart, 1)
            : getCursorRightPosition(selectionEnd, 1, valueLength);

        cursorPositionRef.current = newSelectionStart;
      }
      return;
    }
    event.preventDefault();

    let newValue: string = value;
    if (event.ctrlKey && key === "a") {
      // Select everything when pressing Ctrl + a
      inputTarget.setSelectionRange(0, value.length);
      return;
    } else if ((key >= "0" && key <= "9") || key === "-") {
      // Check if a number key or a decimal point key is pressed
      ({ value: newValue, selectionStart } = handleNumericKey(
        key,
        value,
        selectionStart,
        selectionEnd,
      ));
    } else if (key === "." && (type === "float" || type === "Quantity")) {
      ({ value: newValue, selectionStart } = handleNumericKey(
        key,
        value,
        selectionStart,
        selectionEnd,
      ));
    } else if (key === "ArrowUp" || key === "ArrowDown") {
      ({ value: newValue, selectionStart } = handleArrowKey(
        key,
        value,
        selectionStart,
        // selectionEnd
      ));
    } else if (key === "Backspace") {
      ({ value: newValue, selectionStart } = handleBackspaceKey(
        value,
        selectionStart,
        selectionEnd,
      ));
    } else if (key === "Delete") {
      ({ value: newValue, selectionStart } = handleDeleteKey(
        value,
        selectionStart,
        selectionEnd,
      ));
    } else if (key === "Enter" && !isInstantUpdate) {
      let serializedObject: SerializedObject;
      if (type === "Quantity") {
        serializedObject = {
          type: "Quantity",
          value: {
            magnitude: Number(newValue),
            unit: unit,
          } as QuantityMap,
          full_access_path: fullAccessPath,
          readonly: readOnly,
          doc: docString,
        };
      } else {
        serializedObject = {
          type: type,
          value: Number(newValue),
          full_access_path: fullAccessPath,
          readonly: readOnly,
          doc: docString,
        };
      }

      changeCallback(serializedObject);
      return;
    } else {
      console.debug(key);
      return;
    }

    // Update the input value and maintain the cursor position
    if (isInstantUpdate) {
      let serializedObject: SerializedObject;
      if (type === "Quantity") {
        serializedObject = {
          type: "Quantity",
          value: {
            magnitude: Number(newValue),
            unit: unit,
          } as QuantityMap,
          full_access_path: fullAccessPath,
          readonly: readOnly,
          doc: docString,
        };
      } else {
        serializedObject = {
          type: type,
          value: Number(newValue),
          full_access_path: fullAccessPath,
          readonly: readOnly,
          doc: docString,
        };
      }

      changeCallback(serializedObject);
    }

    setInputString(newValue);

    // Save the current cursor position before the component re-renders
    cursorPositionRef.current = selectionStart;
  };

  const handleBlur = () => {
    if (!isInstantUpdate) {
      // If not in "instant update" mode, emit an update when the input field loses focus
      let serializedObject: SerializedObject;
      if (type === "Quantity") {
        serializedObject = {
          type: "Quantity",
          value: {
            magnitude: Number(inputString),
            unit: unit,
          } as QuantityMap,
          full_access_path: fullAccessPath,
          readonly: readOnly,
          doc: docString,
        };
      } else {
        serializedObject = {
          type: type,
          value: Number(inputString),
          full_access_path: fullAccessPath,
          readonly: readOnly,
          doc: docString,
        };
      }

      changeCallback(serializedObject);
    }
  };
  useEffect(() => {
    // Parse the input string to a number for comparison
    const numericInputString =
      type === "int" ? parseInt(inputString) : parseFloat(inputString);
    // Only update the inputString if it's different from the prop value
    if (value !== numericInputString) {
      setInputString(value.toString());
    }

    // emitting notification
    let notificationMsg = `${fullAccessPath} changed to ${props.value}`;
    if (unit === undefined) {
      notificationMsg += ".";
    } else {
      notificationMsg += ` ${unit}.`;
    }
    addNotification(notificationMsg);
  }, [value]);

  useEffect(() => {
    // Set the cursor position after the component re-renders
    const inputElement = document.getElementsByName(id)[0] as HTMLInputElement;
    if (inputElement && cursorPositionRef.current !== null) {
      inputElement.setSelectionRange(
        cursorPositionRef.current,
        cursorPositionRef.current,
      );
    }
  });

  return (
    <div className="component numberComponent" id={id}>
      {process.env.NODE_ENV === "development" && <div>Render count: {renderCount}</div>}
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
          onChange={() => {}}
          name={id}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          className={isInstantUpdate && !readOnly ? "instantUpdate" : ""}
        />
        {unit && <InputGroup.Text>{unit}</InputGroup.Text>}
      </InputGroup>
    </div>
  );
});

NumberComponent.displayName = "NumberComponent";
